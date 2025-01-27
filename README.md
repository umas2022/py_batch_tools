# py_batch_tools
python 批处理脚本合集，调用各目录下的call.py

## deploy

- windows

```bash
# 安装虚拟环境工具
pip install virtualenv
# 创建虚拟环境（python3.10）
python -m venv venv
# 激活虚拟环境
.\venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
# 冻结虚拟环境
pip freeze > requirements.txt
```


## 功能

- auto
    - auto_still_check

- copy
    - copy_basic
    - copy_img_mirage
    - copy_merge
    - copy_update

- remove
    - remove_difference
    - remove_duplicate_img
    - remove_keyword

- rename
    - rename_prefix_add
    - rename_prefix_del
