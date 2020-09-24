import os
from urllib import parse
import zipfile
import re
import requests
from src.config.config_prep import cfg_prep


def zip_file_name_from_url(data_url, data_dir):
    data_url_str = data_url.split('/')
    filename = parse.unquote(data_url_str[-1])
    zipfile_path = os.path.join(data_dir, filename)
    unzip_dir = os.path.join(data_dir, filename[0:-4])
    return zipfile_path, unzip_dir


def unzip_nested_zip(dataset_zip, path_unzip):
    """ Extract a zip file including any nested zip files"""
    with zipfile.ZipFile(dataset_zip, 'r') as zfile:
        zfile.extractall(path=path_unzip)
    for root, dirs, files in os.walk(path_unzip):
        for filename in files:
            if re.search(r'\.zip$', filename):
                file_spec = os.path.join(root, filename)
                new_dir = os.path.join(root, filename[0:-4])
                unzip_nested_zip(file_spec, new_dir)


def is_there_file(zipfile_path, unzip_dir):
    """if a file has existed"""
    if os.path.isfile(zipfile_path):
        # 如果存在zip文件就不用下载了，直接解压即可
        if os.path.isdir(unzip_dir):
            # 如果已经解压了就啥也不用做了
            return True
        unzip_nested_zip(zipfile_path, unzip_dir)
        return True


def download_small_file(data_url, temp_file):
    """根据url下载数据到temp_file中"""
    r = requests.get(data_url)
    with open(temp_file, 'w') as f:
        f.write(r.text)


def download_one_zip(data_url, data_dir):
    """download one zip file from url as data_file"""
    zipfile_path, unzip_dir = zip_file_name_from_url(data_url, data_dir)
    if not is_there_file(zipfile_path, unzip_dir):
        if not os.path.isdir(unzip_dir):
            os.mkdir(unzip_dir)
        r = requests.get(data_url, stream=True)
        with open(zipfile_path, "wb") as py_file:
            for chunk in r.iter_content(chunk_size=1024):  # 1024 bytes
                if chunk:
                    py_file.write(chunk)
        unzip_nested_zip(zipfile_path, unzip_dir), download_small_file


if not os.path.isdir(cfg_prep.GAGES_PATH):
    os.makedirs(cfg_prep.GAGES_PATH)
[download_one_zip(attr_url, cfg_prep.GAGES.GAGES_PATH) for attr_url in cfg_prep.GAGES.attrUrl]
