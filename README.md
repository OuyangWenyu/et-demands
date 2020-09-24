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

基本步骤如下：

1. 下载各类型数据：USDA CDL 数据，GAGES-II流域数据，NOAA RefET数据，usbr/et-demands 预处理好的 STATSGO 数据。
2. 预处理数据为crop ET（ETc） 计算可用数据：流域内统计计算，并生成一些必要的静态文件。
3. 基于 usbr/et-demands 的方法计算 ETc
4. 后处理：绘图、统计等以验证自己计算无错。

代码编写过程中，尽量不改原来的代码，用到的代码都重新复制粘贴到新文件夹中编写。

#### Multiprocessing

The ET scripts support basic multiprocessing that can be enabled using "-mp N" argument, where N is number of cores to use.  If N is not set, script will attempt to use all cores.  For each ET cell, N crops will be run in parallel.  Using multiprocessing will typically be must faster, but speed improvement may not scale linearly with number of cores because processes are all trying to write to disk at same time.
Multiprocessing is not available for single met node reference et runs or for single et cell area et runs.
Multiprocessing is not available for some output formats.

```
> python run_cet.py -i example.ini -mp
```
