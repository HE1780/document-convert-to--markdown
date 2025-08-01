# MarkItDown 文档转换工具

基于 Microsoft MarkItDown 库的增强版文档转换工具，支持多种文档格式转换为 Markdown，并提供图片提取、路径修复和格式优化功能。

## ⚡ 快速开始

### 30秒快速体验

```bash
# 1. 克隆并进入项目
git clone https://github.com/HE1780/document-convert-to--markdown.git && cd document-convert-to--markdown

# 2. 一键安装
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 3. 立即转换文件
python main.py your_document.pdf
```

转换完成！查看 `output/` 目录中的 Markdown 文件和提取的图片。

### 常用命令

```bash
# 转换单个文件
python main.py document.pdf

# 批量转换目录
python main.py input_folder/

# 启用详细输出
python main.py document.pdf --verbose

# 启用 AI 图片描述
python main.py document.pdf --enable-llm
```

## 🚀 功能特性

- **多格式支持**: PDF, Word, PowerPoint, Excel, 图片, 音频, 网页等 20+ 种格式
- **智能图片处理**: 自动提取和保存文档中的图片，支持 base64 和 URL 图片
- **智能图片引用匹配**: 支持多种图片引用格式的智能识别和匹配
  - 严格格式匹配："图 X-Y"、"表 X-Y"、"Figure X-Y" 等带数字的精确引用
  - 关键词匹配："如图"、"见图"、"流程图"、"示意图" 等常见引用表达
  - 上下文智能定位：基于关键词和上下文信息进行图片位置推断
- **LLM 集成**: 可选集成 OpenAI GPT 或 Anthropic Claude 进行图片描述生成
- **Azure 文档智能**: 支持 Azure Document Intelligence 进行高质量 PDF 处理
- **批量转换**: 支持单文件和目录批量转换
- **详细日志**: 完整的转换过程日志记录和性能统计
- **路径管理**: 智能的文件路径处理和安全检查

## 📋 支持的文件格式

支持 **20+ 种**常见文档格式，包括：

- **📄 文档类**: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS
- **🖼️ 图片类**: PNG, JPG, JPEG, GIF, BMP, TIFF, WEBP  
- **🎵 音频类**: WAV, MP3（语音转录）
- **🌐 网页类**: HTML, HTM, XML
- **📊 数据类**: CSV, TSV, JSON
- **📝 文本类**: TXT, RTF, MD, MARKDOWN
- **📦 其他类**: ZIP, YouTube URLs, EPub

> 💡 **提示**: 详细的格式支持和特殊功能请参考下方的[详细使用指南](#📖-详细使用指南)

## 🛠️ 安装部署

### 环境要求

- Python 3.8+
- macOS / Linux / Windows
- 虚拟环境（推荐）

### 📦 依赖管理说明

本项目采用标准的 Python 包管理方式：

- **MarkItDown 核心库**: 通过 `markitdown[all]>=0.1.2` 依赖包引入，包含所有可选功能
- **项目增强功能**: `src/` 目录包含图片处理、路径管理等增强代码
- **依赖隔离**: 所有依赖安装在虚拟环境中，不影响系统环境

> 💡 **注意**: 项目不包含 MarkItDown 源代码，而是作为依赖包安装

### 快速安装

```bash
# 1. 克隆项目
git clone https://github.com/HE1780/document-convert-to--markdown.git
cd document-convert-to--markdown

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 创建input目录（如需要）
mkdir -p input

# 5. 验证安装
python test_markitdown.py
```

### 可选配置

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件配置可选功能：

```env
# LLM 集成（可选）
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Azure 文档智能（可选）
AZURE_DOC_INTEL_ENDPOINT=your_azure_endpoint
AZURE_DOC_INTEL_KEY=your_azure_key

# 应用配置
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=100
CONCURRENT_WORKERS=4
```

## 📖 详细使用指南

### 🎯 快速使用场景

#### 场景1：转换单个文档
```bash
# 激活环境并转换
source .venv/bin/activate
python main.py document.pdf

# 结果：
# ✅ output/document.md - 转换后的 Markdown 文件
# ✅ output/images/document/ - 提取的图片文件夹
```

#### 场景2：批量转换文档
```bash
# 创建 input/ 目录（如果不存在）
mkdir -p input

# 将所有文档放入 input/ 目录，然后批量转换
python main.py input/

# 或指定自定义目录
python main.py /path/to/your/documents/
```

#### 场景3：高质量 PDF 转换
```bash
# 使用 Azure 文档智能服务（需配置 API）
python main.py document.pdf --use-azure-doc-intel
```

#### 场景4：AI 增强图片描述
```bash
# 使用 OpenAI 或 Claude 生成图片描述（需配置 API）
python main.py document.pdf --enable-llm
```

#### 场景5：智能图片引用匹配
```bash
# 系统自动识别文档中的图片引用并智能插入
# 支持的引用格式：
# - "图 2-1"、"表 3-2"、"Figure 1.1" 等精确格式
# - "如图所示"、"见图"、"流程图"、"示意图" 等关键词
# - "诊疗流程"、"上图"、"下图" 等上下文表达
python main.py document.pdf --verbose
```

### 🛠️ 命令行参数详解

```bash
# 基础转换
python main.py <文件或目录路径>

# 可选参数
--verbose              # 显示详细转换过程
--enable-llm          # 启用 AI 图片描述生成
--use-azure-doc-intel # 使用 Azure 文档智能
--keep-data-uris      # 保留 base64 图片数据
--help                # 显示帮助信息
```

### 📋 支持的输入格式

| 文档类型 | 扩展名 | 特殊说明 |
|----------|--------|----------|
| **Office文档** | `.docx`, `.doc`, `.pptx`, `.ppt`, `.xlsx`, `.xls` | 自动提取图片和表格 |
| **PDF文档** | `.pdf` | 支持 OCR 和 Azure 智能解析 |
| **图片文件** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.webp` | 支持 OCR 文字识别 |
| **网页文件** | `.html`, `.htm`, `.xml` | 提取文本和图片 |
| **数据文件** | `.csv`, `.tsv`, `.json` | 转换为 Markdown 表格 |
| **文本文件** | `.txt`, `.rtf`, `.md` | 直接转换或格式化 |
| **其他** | YouTube URL, `.zip` | 在线内容和压缩包处理 |

### 直接使用 MarkItDown

```bash
# 使用原生 MarkItDown 命令
markitdown document.pdf

# 输出到文件
markitdown document.pdf -o output.md

# 查看帮助
markitdown --help
```

### Python API 使用

```python
from src.converter import DocumentConverter
from src.config import Config

# 初始化转换器
converter = DocumentConverter(
    enable_llm=False,
    use_azure_doc_intel=False,
    keep_data_uris=False
)

# 转换单个文件
result = converter.convert_file("document.pdf")
print(f"转换完成: {result['output_file']}")

# 批量转换
results = converter.convert_directory("input_folder/")
print(f"转换了 {len(results)} 个文件")
```

## 📁 项目结构

```
markitdown/
├── .env.example              # 环境变量模板
├── .venv/                    # Python 虚拟环境（不可移植）
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖包列表
├── test_markitdown.py       # 部署测试脚本
├── README.md                # 项目说明文档
├── WORK_PROGRESS.md         # 工作进度文档
├── 开发方案.md               # 开发方案文档
├── PRD.md                   # 产品需求文档
├── src/                     # 源代码目录（项目核心）
│   ├── config.py            # 配置管理
│   ├── converter.py         # 文档转换器
│   ├── document_processors.py # 文档处理器（架构重构）
│   ├── image_processor.py   # 图片处理器
│   ├── logger.py            # 日志管理器
│   └── path_manager.py      # 路径管理器
├── input/                   # 输入文件目录
├── output/                  # 输出文件目录
├── images/                  # 提取的图片目录
├── temp/                    # 临时文件目录
└── logs/                    # 日志文件目录
```

## 🚀 项目可移植性

### ✅ 可移植文件
- 所有源代码文件（`src/`, `main.py` 等）
- 配置文件（`requirements.txt`, `.env.example`）
- 文档文件（`README.md`, `*.md`）
- 测试脚本（`test_*.py`）

### ❌ 不可移植文件
- `.venv/` 虚拟环境（包含绝对路径）
- `output/`, `temp/`, `logs/` 运行时生成的目录

### 📋 移植步骤

```bash
# 1. 拷贝项目（排除虚拟环境）
rsync -av --exclude='.venv' --exclude='temp' --exclude='logs' \
      --exclude='output' markitdown/ /target/path/

# 2. 在目标电脑重新创建环境
cd /target/path/markitdown
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 验证安装
python test_markitdown.py
```

### 🔧 系统要求
- **Python**: 3.8+ 版本
- **磁盘空间**: 至少 500MB（包含所有依赖）
- **网络**: 首次安装需要下载依赖包
- **权限**: 读写项目目录的权限

## 🔧 配置说明

### 基础配置

- `INPUT_DIR`: 输入文件目录（默认: input）
- `OUTPUT_DIR`: 输出文件目录（默认: output）
- `IMAGES_DIR`: 图片保存目录（默认: images）
- `TEMP_DIR`: 临时文件目录（默认: temp）

### 文件处理配置

- `MAX_FILE_SIZE`: 最大文件大小（默认: 100MB）
- `SUPPORTED_FORMATS`: 支持的文件格式列表
- `CONCURRENT_WORKERS`: 并发处理线程数（默认: 4）

### 图片处理配置

- `IMAGE_QUALITY`: 图片质量（默认: 85）
- `MAX_IMAGE_SIZE`: 最大图片尺寸（默认: 1920x1080）
- `IMAGE_FORMATS`: 支持的图片格式

### 日志配置

- `LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `LOG_TO_FILE`: 是否记录到文件（默认: True）
- `LOG_TO_CONSOLE`: 是否输出到控制台（默认: True）

## 🧪 测试验证

### 运行测试脚本

```bash
# 完整测试
python test_markitdown.py

# 测试单个文件转换
python main.py test_document.txt --verbose

# 测试 MarkItDown 原生功能
markitdown test_document.txt
```

### 测试覆盖范围

- ✅ MarkItDown 库安装验证
- ✅ 基本转换功能测试
- ✅ 支持格式检查
- ✅ LLM 集成配置检查
- ✅ Azure 文档智能配置检查
- ✅ 项目结构完整性验证

## 🏗️ 技术架构

### 架构重构亮点

本项目经过完整的架构重构，实现了**完全分离的文档处理架构**：

#### 🔧 核心组件

- **`BaseDocumentProcessor`**: 抽象基类，定义统一接口和通用方法
- **`WordDocumentProcessor`**: 专门处理Word文档图片提取
- **`PDFDocumentProcessor`**: 专门处理PDF文档，包含智能插入功能
- **`ImageDocumentProcessor`**: 专门处理图片文件，支持图片到Markdown的转换
- **`DocumentProcessorFactory`**: 工厂类，根据文件类型创建相应处理器
- **`ImageProcessor`**: 重构为协调器角色，通过委托实现功能

#### ✨ 技术特点

- **完全分离**: Word、PDF和图片处理逻辑完全独立，避免相互干扰
- **图片文件支持**: 支持单个图片文件转换为Markdown格式，包含OCR文字识别
- **一致性**: 文件命名、存储位置和输出位置保持统一
- **可维护性**: 清晰的类结构，易于扩展和维护
- **向后兼容**: 保持原有接口，不影响现有调用
- **错误处理**: 添加了详细的调试日志和错误处理机制

#### 🧪 验证结果

- **Word文档**: 成功提取88张图片，图片在正确位置显示
- **PDF文档**: 成功提取102张图片，智能插入功能正常工作
- **图片存储**: 统一的命名规则和目录结构

## 📊 性能特性

- **并发处理**: 支持多线程并发转换，提高批量处理效率
- **内存优化**: 智能内存管理，避免大文件处理时的内存溢出
- **进度显示**: 实时显示转换进度和性能统计
- **错误恢复**: 单个文件转换失败不影响批量处理继续进行
- **缓存机制**: 智能缓存机制，避免重复转换相同文件
- **智能插入**: PDF文档支持基于引用模式的智能图片插入

## 🔒 安全特性

- **路径安全**: 严格的路径验证，防止目录遍历攻击
- **文件大小限制**: 可配置的文件大小限制，防止资源耗尽
- **格式验证**: 严格的文件格式验证，防止恶意文件处理
- **权限控制**: 最小权限原则，仅访问必要的文件和目录

## 🚨 故障排除

### ⚡ 快速解决方案

| 问题症状 | 快速解决 | 详细说明 |
|----------|----------|----------|
| `ModuleNotFoundError` | `source .venv/bin/activate && pip install -r requirements.txt` | 虚拟环境未激活或依赖未安装 |
| `Permission denied` | `chmod 755 output/` | 输出目录权限不足 |
| `File format not supported` | 检查文件扩展名是否在支持列表中 | 参考上方支持格式表格 |
| `Memory error` | `export PYTHONHASHSEED=0` 或处理较小文件 | 内存不足，建议分批处理 |
| 图片无法显示 | 检查 `output/images/` 目录和相对路径 | 确保图片文件存在且路径正确 |
| 转换速度慢 | 使用 `--verbose` 查看进度 | 大文件需要更多时间 |

### 🔍 调试命令

```bash
# 详细模式查看转换过程
python main.py document.pdf --verbose

# 测试安装是否正确
python test_markitdown.py

# 查看实时日志
tail -f logs/markitdown.log

# 检查文件权限
ls -la output/
```

### 📞 获取帮助

```bash
# 查看所有可用参数
python main.py --help

# 查看 MarkItDown 原生帮助
markitdown --help

# 运行测试验证环境
python test_markitdown.py
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) - 核心转换库
- [OpenAI](https://openai.com/) - LLM 集成支持
- [Azure Document Intelligence](https://azure.microsoft.com/services/form-recognizer/) - 文档智能服务

## 📞 支持

如果您遇到问题或有功能建议，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

---

**版本**: 1.1.0 (架构重构版)  
**最后更新**: 2025-08-02  
**维护者**: Assistant  
**重构完成**: ✅ 文档处理架构完全分离

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目基于 MIT 许可证开源。详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Microsoft MarkItDown](https://github.com/microsoft/markitdown) - 核心转换库
- 所有贡献者和用户的支持

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 [Issue](https://github.com/your-repo/markitdown/issues)
- 发送邮件至：your-email@example.com

---

## 📋 快速参考卡片

### 🚀 一键命令
```bash
# 快速安装
git clone <repo> && cd markitdown && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 常用转换
python main.py document.pdf                    # 基础转换
python main.py input/ --verbose               # 批量转换（详细模式）
python main.py document.pdf --enable-llm      # AI 增强转换

# 项目移植
rsync -av --exclude='.venv' markitdown/ /target/  # 拷贝项目
cd /target/markitdown && python3 -m venv .venv    # 重建环境
```

### 📁 重要目录
- `input/` - 放置待转换文件
- `output/` - 查看转换结果
- `output/images/` - 提取的图片
- `logs/` - 转换日志
- `.env` - 配置文件

### 🔧 环境配置
```bash
# 必需
source .venv/bin/activate

# 可选（AI 功能）
export OPENAI_API_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"
export AZURE_DOC_INTEL_ENDPOINT="your_endpoint"
export AZURE_DOC_INTEL_KEY="your_key"
```

### 🆘 遇到问题？
1. 运行 `python test_markitdown.py` 检查环境
2. 使用 `--verbose` 查看详细过程
3. 查看 `logs/markitdown.log` 日志文件
4. 提交 [Issue](../../issues/new) 获取帮助

---

**Happy Converting! 🚀**