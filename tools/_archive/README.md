# _archive

这些是**一次性脚本**，任务已完成，留档只为追溯当时怎么做的。

⚠️ 不要直接运行：它们大多基于当时 app.py 的锚点字符串，
   文件已经改过多轮，再跑会失败或改错文件。

其中几个记录了本轮踩过的真坑，值得保留：
- repair_i18n_zh_tw.py / rebuild_i18n_zh_tw.py / finalize_i18n_zh_tw.py
   繁体语言包被补丁脚本写坏（少了收尾括号）后的抢救与重建过程
- wrap_ui_strings.py / wrap_prompt_strings.py / wrap_last_strings.py
   把界面文案包上 t() 的机械改写（每个都带语法检查 + 失败回滚）
- renumber_questions.py
   新增问题后题号错乱（出现两个 5）的修复 —— 按顺序重排而非逐个替换
- strip_bom.py
   去掉 PowerShell 写出的 BOM

长期在用的是 tools/ 下的：
  check_encoding.py / check_i18n.py / check_option_uniqueness.py
  selftest_*.py / screenshot.py / screenshot_langs.py
  generate_sample.py / s2t.py
