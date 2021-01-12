[![Documentation Status](https://readthedocs.org/projects/cet-demands/badge/?version=latest)](https://cet-demands.readthedocs.io/zh_CN/latest/?badge=latest)
[![Build Status](https://travis-ci.org/OuyangWenyu/et-demands.svg?branch=master)](https://travis-ci.org/github/OuyangWenyu/et-demands)
[![Coverage Status](https://coveralls.io/repos/github/OuyangWenyu/et-demands/badge.svg?branch=master)](https://coveralls.io/github/OuyangWenyu/et-demands?branch=master)

# CropET

本项目基于 [usbr/et-demands](https://github.com/usbr/et-demands)，计算GAGES-II流域对应的历史（暂定2008-2017）农作物蒸散发数据（暂定日尺度）.

正在开发中。。。

## Documentation

文档基于原文档[Manual and Documentation](http://et-demands.readthedocs.io/en/master)，添加我自己需要的部分：[文档手册](https://cet-demands.readthedocs.io/)。

## Dependencies

安装依赖环境，直接使用environment.yml即可：

```
> conda env create -f environment.yml
```

After creating the environment, it then needs to be "activated":

```
conda activate etdemands
```

## Introduction

因为我是针对流域计算的，所以我主要参考的原来代码的 examples/huc8 文件夹下的内容。即逐步学习 model_commands.txt 中命令对应的代码。

然后修改为我需要的版本。

修改时基本步骤如下：

1. 下载各类型数据：USDA CDL 数据，GAGES-II流域数据，NOAA RefET数据（现在换成GRIDMET forcing数据），usbr/et-demands 预处理好的 STATSGO 数据。
2. 预处理数据为crop ET（ETc） 计算可用数据：流域内统计计算（以GEE版本为主），并生成一些必要的静态文件。
3. 基于 usbr/et-demands 的方法计算 ETc
4. 后处理：绘图、统计等以验证自己计算无错。

代码编写过程中，尽量不改原来的代码，用到的代码都重新复制粘贴到新文件夹中编写。

修改之后，运行代码步骤如下（注意重点参考prep/preprocess4gages文件夹下的 commands_seq.txt）：

1. 下载好 GAGES-II 数据，代码在：src/prep/download_data/download_gagesii.py
2. 下载计算好的流域平均 GRIDMET forcing data，这部分目前需要手动处理，文件都在自己google drive上，文件放在examples/common/gridmet 文件夹中；
3. 处理 forcing 数据到 Daymet 的格式，使用代码：src/prep/preprocess4gages/trans_gridmet_to_basin_files.py，注意not_trans_yet 设置为True
4. 选择部分流域，需要首先调用 src/prep/preprocess4gages/rebuild_shpfile.py 来构建属于这些被选中的流域的一个统一的shapefile，放到对应项目文件夹中
5. 接下来根据选择的流域构成的id，抽取对应的forcing data到 region文件夹的climate子文件夹中，代码在：src/prep/preprocess4gages/trans_gridmet_to_basin_files.py，注意not_trans_yet 设置为False
6. 计算各个流域中作物的类型和对应的面积，一批批流域处理以防报错（debug总有错，因此需要直接run）。有GEE计算，但是按照GEE的格式后面调整蛮多。
   - 下载CDL数据，使用src/prep/preprocess4gages/download_cdl_raster.py 
   - 先将CDL数据切割到各流域，调用代码：src/prep/preprocess4gages/clip_cdl_raster_to_gages.py
   - 构建切割的数据的shpfile：src/prep/preprocess4gages/build_ag_cdl_in_gages_region_shapefile.py
   - 下载 Soils Files，虽然我没用到，但是为了跑通这个代码，需要下载下来：src/prep/download_data/download_statsgo_shapefiles.py
   - 统计各流域作物类型及面积：src/prep/preprocess4gages/et_demands_gages_region_stats.py
7. 把 build_static_files_for_gages.py 
8. 计算cropet：调用 src/cropet4gages/gages_crop_et.py 计算

但是上述过程还是会碰到数据过大的情况，所以还是使用 GEE 的结果来进行计算了。以下是GEE

1. 和上面的前三步一样，下载并准备数据；此外，还需要把自己在GEE上处理的 作物面积数据 下载到 examples/common/usda_cdl 文件夹里
2. 用 src/prep/preprocess4gages/et_demands_gages_region_stats.py 里的代码，用GEE模式的code，把上面的统计信息加入到shpfile中
3. 跑一下 build_static_files_for_gages.py 生成静态文件
4. 运行 src/cropet4gages/gages_crop_et.py 计算 crop ET

#### Multiprocessing

TODO：多进程暂时还未处理

```
> python run_cet.py -i example.ini -mp
```
