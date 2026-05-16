# 翻译结果归档功能

## 功能说明

翻译完成后，自动将翻译结果归档到源文件路径，支持：
- ✅ 单图文件：直接复制翻译后的图片
- ✅ 文件夹图片：复制整个结果目录
- ✅ 压缩包（ZIP/CBZ/PDF/EPUB）：打包成压缩包

## 核心功能

### 1. 自动补全缺失文件
在归档前，自动检查 `result` 目录是否完整：
- 比较 `original_images` 和 `result` 目录的文件数量
- 自动复制缺失的原图到 `result` 目录
- 确保归档的文件是完整版本

### 2. 智能归档
根据源文件类型自动选择归档方式：
- **压缩包源文件**：将 `result` 目录打包成压缩包
- **文件夹源文件**：复制整个 `result` 目录
- **单图源文件**：复制翻译后的图片文件

### 3. 自定义命名
- 默认前缀：`[#trans]`
- 可自定义前缀
- 示例：`test.zip` → `[#trans]test.zip`

## 配置选项

在设置界面的 "General" 标签页中：

### 归档结果到源路径
- **选项名称**：`app.archive_result_to_source`
- **默认值**：`false`
- **说明**：翻译完成后将结果归档到源文件路径

### 归档文件名前缀
- **选项名称**：`app.archive_result_prefix`
- **默认值**：`[#trans]`
- **说明**：归档文件名的前缀

### 归档后删除结果目录
- **选项名称**：`app.delete_result_after_archive`
- **默认值**：`false`
- **说明**：归档完成后删除翻译结果目录，节省磁盘空间

## 使用流程

### 1. 启用归档功能
在设置中勾选 "归档结果到源路径"

### 2. 翻译文件
正常翻译文件，支持：
- 单图文件
- 文件夹中的图片
- 压缩包文件（ZIP/CBZ/PDF/EPUB）

### 3. 自动归档
翻译完成后，自动执行：
1. 检查 `result` 目录是否完整
2. 补全缺失的原图
3. 根据源文件类型归档
4. （可选）删除结果目录

## 示例

### 单图文件
```
源文件: E:\manga\test.jpg
翻译结果: E:\output\test\result\test.jpg
归档结果: E:\manga\[#trans]test.jpg
```

### 文件夹图片
```
源文件夹: E:\manga\chapter1\
翻译结果: E:\output\chapter1\result\
归档结果: E:\manga\[#trans]chapter1\
```

### 压缩包
```
源文件: E:\manga\chapter1.zip
翻译结果: E:\output\chapter1\result\
归档结果: E:\manga\[#trans]chapter1.zip
```

## 技术实现

### 文件结构
```
output/
├── test/
│   ├── .archive_source.txt    # 记录源文件路径
│   ├── original_images/        # 原图目录
│   │   ├── 001.jpg
│   │   ├── 002.jpg
│   │   ├── 003.jpg
│   │   └── manga_translator_work/
│   │       └── result/         # 翻译结果目录（实际位置）
│   │           ├── 001.jpg    # 翻译后的图片
│   │           ├── 002.jpg
│   │           └── 003.jpg
│   └── result/                 # 翻译结果目录（兼容旧版本）
```

### 关键文件
- `.archive_source.txt`：记录源文件路径，用于归档时找到源文件
  - 位置：`original_images` 的父目录
  - 示例：`output/test/.archive_source.txt`
- `original_images/`：原图目录，用于补全缺失文件
- `result/`：翻译结果目录，归档的源数据
  - 可能在 `original_images/manga_translator_work/result` 下
  - 也可能在 `output/test/result` 下（兼容旧版本）

### 补全逻辑
1. 读取 `original_images` 目录中的所有图片文件
2. 读取 `result` 目录中的所有图片文件
3. 计算缺失的文件（在 `original_images` 中但不在 `result` 中）
4. 复制缺失的文件到 `result` 目录

### 归档逻辑
1. 检查源文件类型（压缩包/文件夹/单图）
2. 根据类型选择归档方式：
   - 压缩包：创建 ZIP 文件
   - 文件夹：复制整个目录
   - 单图：复制单个文件
3. 添加前缀到文件名
4. 放置到源文件所在目录

## 注意事项

1. **源文件路径**：确保 `.archive_source.txt` 文件中的路径正确
2. **磁盘空间**：归档会占用额外的磁盘空间
3. **文件覆盖**：如果目标文件已存在，会跳过归档
4. **删除结果目录**：建议确认归档成功后再启用此选项

## 错误处理

- 源文件不存在：跳过归档
- 结果目录不存在：跳过归档
- 输出文件已存在：跳过归档
- 复制/打包失败：记录错误日志
