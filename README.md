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
    - 窗口静态检测 

- copy
  - copy_basic
    - 简单拷贝
  - copy_gif_frame
    - 提取gif中的帧
  - copy_img_mirage
    - 图片生成幻影坦克
  - copy_img_resize
    - 图片压缩裁剪
  - copy_img_rotate
    - 图片旋转
  - copy_img_to_bmp
    - 图片转bmp格式
  - copy_img_to_gif
    - 图片合成gif
  - copy_image_to_jpeg
    - 图片转jpeg格式
  - copy_merge
    - 拷贝合并，展平内部文件结构
  - copy_psd_to_png
    - psd导出png
  - copy_update
    - 拷贝升级，仅拷贝有变化的文件
  - copy_vid_cut_size
    - 视频尺寸剪裁（仅裁剪，不压缩）
  - copy_vid_cut_time
    - 视频时长裁剪
  - copy_vid_frame
    - 视频提取帧图片
  - copy_vid_resize
    - 视频尺寸压缩裁剪

- remove
  - remove_difference
    - 删除差异文件
  - remove_duplicate_img
    - 删除重复图片
  - remove_keyword
    - 删除包含关键字的文件

- rename
  - rename_by_num
    - 按数字序号命名
  - rename_prefix_add
    - 增加前缀
  - rename_prefix_del
    - 删除前缀
