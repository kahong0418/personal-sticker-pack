# Personal Sticker Pack · 把自己做成 WhatsApp sticker

一个 Claude Code skill：给它几张你的照片，它带你做出**一看就认得是你**的漫画风 sticker，打包成 WhatsApp 规格的图，再用 sticker app 加进 WhatsApp。也能做情侣、朋友、团队一起入镜的 sticker。

[English below](#english)

## 它帮你做什么

1. **挑照片**：教你挑哪几张最好用，再帮你找出你的「辨识记号」，例如平头加粗框眼镜。
2. **挑风格和表情**：三种实测过的风格（可爱 Q 版、搞笑 Meme、共鸣韩漫），加五种备选；每种附 12 个表情清单。
3. **写出图工单**：生成一份 brief，贴进 ChatGPT（附上照片）、交给 Codex，或任何能吃参考图的出图工具都能用。
4. **打包**：一支脚本把出来的图变成 512×512 的 sticker，每张 WebP 压到 100KB 以下，再做托盘图标和总览图。
5. **检查和安装**：逐张核像不像你、手指对不对、字有没有画糊，再一步步教你加进 WhatsApp。

⚠️ Claude 本身不出图。出图要用你自己的 ChatGPT、Codex 或其他出图工具。

## 安装（macOS / Linux）

```bash
git clone https://github.com/kahong0418/personal-sticker-pack.git
mkdir -p ~/.claude/skills
cp -r personal-sticker-pack/personal-sticker-pack ~/.claude/skills/
python3 -m pip install pillow
```

Windows：把 repo 里的 `personal-sticker-pack` 资料夹复制到 `%USERPROFILE%\.claude\skills\`，再跑 `py -m pip install pillow`。

装好后在 Claude Code 讲一句「帮我做我的 sticker」，再附上照片就可以开始。

## 只想用打包脚本

```bash
python3 ~/.claude/skills/personal-sticker-pack/scripts/pack.py 我的图/ 输出/ --name "我的 sticker"
```

出图工具没给透明底也没关系：纯白或纯色背景会自动去掉，再补一圈白边。照片、渐层或假的棋盘格背景去不掉，脚本会叫你重出那张。

## 隐私

这个 skill 本身不会上传任何东西。但是照片会让 Claude 读，也会传到你选的出图工具（ChatGPT、Codex 等）。成品留在你自己的电脑上。用别人的样子（另一半、朋友）之前，先问过对方。

---

## English

A Claude Code skill that turns a few photos of you into an illustrated sticker pack that still looks like you, sized to WhatsApp's rules (512×512 WebP under 100KB, 96×96 tray icon), then added to WhatsApp with a sticker app. Works for couples and groups too.

It walks you through: choosing reference photos and naming your identity markers → picking a style (three tested: chibi, meme cartoon, webtoon with captions; five alternatives) and an expression list → writing a generation brief for ChatGPT, Codex or any image model that accepts reference photos → packing with `scripts/pack.py` → checking each sticker and installing it in WhatsApp.

Claude does not generate the images itself; you use your own image tool.

**Install (macOS / Linux):** `mkdir -p ~/.claude/skills`, copy `personal-sticker-pack/` into it, then `python3 -m pip install pillow`. On Windows copy it to `%USERPROFILE%\.claude\skills\` and run `py -m pip install pillow`. Then ask Claude Code to "make stickers of me".

**Privacy:** the skill uploads nothing by itself, but your photos are read by Claude and sent to the image tool you choose. Ask before using anyone else's face.

## License

MIT
