# Everything Skill

这是一个遵循通用 Agent Skills 目录约定的 Windows 全机文件搜索 Skill。它通过 Voidtools Everything 的 `es.exe` 查询现有索引，并提供 UTF-8 输出、默认结果限制和 offset 分页。

项目不依赖任何特定 Agent 或 Harness。运行时文件均基于 Skill 自身目录定位。

## 运行要求

- Windows
- Python 3.10 或更高版本
- Windows 自带的 Windows PowerShell 5.1，或 PowerShell 7+
- 已安装、完成索引并正在运行的 [Everything](https://www.voidtools.com/)
- 当前 Agent 或 sandbox 的执行环境能够访问 Everything IPC

需要注意的是，Agent 能读取 Skill 文件，不等于其 sandbox 一定能连接宿主机 Everything。IPC 不可达时，ES 返回码 `8` 也可能表示 Everything 未运行、命名实例不匹配或执行环境隔离，而不一定表示未安装。

## 安装

可以将下面的消息直接发送给支持 Agent Skills 的 Agent：

> # 请安装 Everything Skill
>
> 1. 将 `https://github.com/SsuJojo/everything-skill.git` 克隆到当前 Agent 的 Skills 目录，最终目录名设为 `everything`。
> 2. 将其作为 Agent Skill 加载。仅清理克隆得到的安装副本：
>    - 可删除不参与运行的仓库与开发文件：`.git/`、`.github/`、`.gitattributes`、`.gitignore`、`tests/` 和 `README.md`。
>    - 必须保留完整的运行时内容：`SKILL.md`、`scripts/`、`bin/`、`references/`、`licenses/` 和可选的 `agents/`；不要删除其他文件。
> 3. 阅读 `SKILL.md` 中的 Requirements，并运行 `scripts/ensure-everything-tools.ps1`，检查 bundled ES、系统架构和 Everything IPC 是否可用。
> 4. 不要自动安装 Everything 主程序。如果 bundled ES 缺失或不兼容，在使用 `-AllowDownload` 修复前先征得用户同意。
> 5. 验证成功后报告 Skill 的安装目录、ES 版本和 IPC 状态，并标记为已配置；如果失败，报告 helper 返回的消息和退出码。

也可以手动安装：将仓库克隆或完整复制到 Agent 的 Skills 位置，并将最终目录命名为 `everything`：

```text
<agent-skills>/everything/SKILL.md
```

不要只复制 `SKILL.md`，`scripts/`、`bin/`、`references/` 和 `licenses/` 都属于 Skill 运行时。

## 目录结构

```text
everything/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml              # 可选的 OpenAI/Codex UI metadata
├── bin/
│   ├── es.exe                   # bundled ES 1.1.0.37 x64
│   └── es.manifest.json
├── licenses/
│   └── ES-LICENSE.txt
├── references/
│   ├── es-cli.md
│   └── everything-options.md
└── scripts/
    ├── es_wrapper.py
    └── ensure-everything-tools.ps1
```

`agents/openai.yaml` 仅提供可选 UI metadata；核心 Skill 与运行时脚本不会读取或依赖它。

## 快速验证

从仓库根目录执行基本搜索：

```powershell
python scripts/es_wrapper.py --format json -- "*.pdf"
```

诊断 bundled ES 与 Everything IPC（不会自动下载）：

```powershell
powershell.exe -NoProfile -File scripts/ensure-everything-tools.ps1
```

只有在用户同意后，才允许 helper 修复缺失或架构不兼容的 ES：

```powershell
powershell.exe -NoProfile -File scripts/ensure-everything-tools.ps1 -AllowDownload
```

helper 从官方 [`voidtools/ES`](https://github.com/voidtools/ES) 最新 release 选择与 Windows 原生架构匹配的 x86、x64、ARM 或 ARM64 asset。它不会安装 Everything 主程序。

## Wrapper 行为

- 从自身位置解析 `bin/es.exe`
- 将 ES 1.1.0.37 的 `-argv` 放在 ES 参数首位，以支持 Unicode 输入
- 固定使用 `-cp 65001`，使管道中的 stdout 和 stderr 使用 UTF-8
- 默认最多返回 20 行，可通过 `--output-limit` 调整
- 使用 `--offset` 进行简单分页
- 提供 text、json 和 json-pretty 输出
- 将高级 ES 选项与 export 参数直接透传

对于统计、列输出、CSV/JSON 等 ES 原生 stdout，建议使用 `--format text`。完整导出应使用 `--output-limit -1`，并遵循宿主 Harness 正常的文件写入和覆盖确认规则。

通过 `--es-path` 指定的自定义 ES 应与 bundled ES 1.1.0.37 兼容，并支持 `-argv` 与 `-cp 65001`。

## 开发验证

```powershell
python -m unittest discover -s tests -v
powershell.exe -NoProfile -File tests/test_ensure_everything_tools.ps1
```

CI 使用 Windows，并在 Python 3.10 与 3.14 上运行单元测试；helper 测试分别覆盖 Windows PowerShell 5.1 与 PowerShell 7，同时执行 Agent Skills 规范验证。项目不承诺 Python 3.8 兼容。

## 第三方组件

仓库内置 `bin/es.exe` 为 ES 1.1.0.37 x64。其版本、来源、架构和 SHA-256 记录在 `bin/es.manifest.json`，MIT 许可证副本位于 `licenses/ES-LICENSE.txt`。

manifest 只描述仓库或发行包内置的 binary。helper 在本机运行时从 `releases/latest` 修复 ES 后，不会修改 manifest 或其他 Git metadata。

本仓库尚未替项目自有代码选择许可证；第三方 ES 的 MIT License 不自动适用于仓库内其他文件。
