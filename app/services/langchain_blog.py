"""
LangChain チュートリアル用のサンプルワークフロー。
- 1. 意図の把握（理解できない場合は明確化質問を返す）
- 2. アウトライン作成（約4セクション）
- 3. 各セクションを約1000文字で執筆
- 4. 編集者視点で全体を校正し、最終記事を作成

実務寄りの書き方:
- 明確な関数分割
- LLMの入出力を型安全なDTOにマッピング
- LangChain Runnable を用いたステップ設計
"""

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.models.llm import BlogArticleRequest, BlogArticleResponse, BlogSection
from app.services.llm import _build_openai_llm, _build_openrouter_llm


def _select_llm_provider(req: BlogArticleRequest):
    settings = get_settings()
    provider = (req.provider or "openrouter").lower()
    if provider == "openrouter":
        model = req.model or settings.openrouter_model or "openrouter/auto"
        return _build_openrouter_llm(model, 0.3)
    model = req.model or settings.openai_model or "gpt-4o-mini"
    return _build_openai_llm(model, 0.3)


def _intent_prompt(language: str) -> ChatPromptTemplate:
    system = (
        "You are a helpful content strategist. Ask clarifying questions when the\n"
        "user's intent is ambiguous."
    )
    if language == "ja":
        system = (
            "あなたは有能なコンテンツストラテジストです。意図が曖昧な場合は\n"
            "簡潔な確認質問を返してください。"
        )
    template = (
        "ユーザーから与えられたキーワードを分析して、\n"
        "どのような投稿（ブログ記事）をしたいのかを推測してください。\n"
        "必要であれば3問以内の確認質問を出してください。\n\n"
        "入力キーワード: {keyword}\n"
        "想定読者: {audience}\n"
        "文体: {style}\n\n"
        "出力フォーマット(JSON):\n"
        "{{\n"
        '  "need_clarification": <true|false>,\n'
        '  "questions": [<string>...] (省略可),\n'
        '  "intent_summary": <string> (明確化不要の場合のみ)\n'
        "}}"
    )
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=template)]
    )


def _outline_prompt(language: str) -> ChatPromptTemplate:
    system = "You are a senior content planner. Create a clear outline."
    if language == "ja":
        system = "あなたはシニアなコンテンツプランナーです。わかりやすい見出し構成を作成してください。"
    template_head = (
        "以下の意図に基づいて、ブログ記事のセクション見出しを{section_count}個、\n"
        "論理的な順番で作成してください。\n\n"
        "意図の要約: {intent_summary}\n\n"
        "出力フォーマット(JSON):\n"
    )
    json_format = '{\n\t"title": <string>,\n\t"outline": [<string>, <string>, ...]\n}'
    full_template = template_head + json_format
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=full_template)]
    )


def _section_prompt(language: str) -> ChatPromptTemplate:
    system = (
        "You are a professional writer. Write ~1000 Japanese characters per section."
        if language == "ja"
        else "You are a professional writer. Write ~1000 English words per section."
    )
    template = (
        "記事タイトル: {title}\n"
        "セクション見出し: {section_title}\n"
        "想定読者: {audience}\n"
        "文体: {style}\n\n"
        "要件:\n"
        "- 初学者にも分かるように段階的に説明\n"
        "- 例示と比喩を活用\n"
        "- スパン長を調整しつつ約1000文字\n"
        "- セクション内で完結性を高める\n"
        "- ユーザーへ追加情報を要求しない（手持ち情報と常識で補完）\n"
        "- トピックから逸脱しない（主要トピック: {keyword}）\n"
    )
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=template)]
    )


def _editor_prompt(language: str) -> ChatPromptTemplate:
    system = (
        "You are a meticulous editor. Check consistency, flow, typos,"
        " and output the final article."
    )
    if language == "ja":
        system = (
            "あなたは几帳面な編集者です。論理の流れ、つながり、誤字脱字を確認し、\n"
            "最終的な読みやすい記事として整えてください。"
        )
    template = (
        "記事タイトル: {title}\n\n"
        "# セクション本文\n"
        "{sections_text}\n\n"
        "出力: 最終的な記事（見出しと本文を含むMarkdown推奨）\n\n"
        "制約:\n"
        "- トピックから逸脱しない（主要トピック: {keyword}）\n"
        "- ユーザーへの追加質問やテンプレートのままの文言は出力しない\n"
    )
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=template)]
    )


def _critic_prompt(language: str) -> ChatPromptTemplate:
    """Self-Refine/CRITIC: 生成文のトピック整合性・指示遵守を検査する。JSONで返答。"""
    if language == "ja":
        system = "あなたは厳密な内容チェッカーです。トピック整合性と指示遵守を検査してください。"
    else:
        system = (
            "You are a rigorous content critic. Check topic adherence and"
            " instruction compliance."
        )
    template = (
        "主要トピック: {keyword}\n"
        "対象: {audience}\n"
        "制約: トピック逸脱なし / 追加質問なし / 十分な分量 / 明確な日本語\n\n"
        "対象テキスト:\n{content}\n\n"
        "出力(JSON):\n"
        "{\n"
        '  "ok": <true|false>,\n'
        '  "issues": [<string>...],\n'
        '  "suggestion": <string>\n'
        "}"
    )
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=template)]
    )


def _refine_prompt(language: str) -> ChatPromptTemplate:
    """Self-Refine: 批評を踏まえてリライト。"""
    system = (
        "You are an expert editor who revises text according to critique."
        if language != "ja"
        else "あなたは熟練の編集者です。批評に基づきテキストを修正してください。"
    )
    template = (
        "主要トピック: {keyword}\n"
        "対象: {audience}\n"
        "指摘事項:\n{issues}\n\n"
        "元テキスト:\n{content}\n\n"
        "出力要件:\n"
        "- 指摘をすべて解消\n"
        "- 追加質問をせず、情報は補完\n"
        "- トピックから逸脱しない\n"
        "- 約1000文字（日本語の場合）\n\n"
        "新しいテキストのみを出力"
    )
    return ChatPromptTemplate.from_messages(
        [SystemMessage(content=system), HumanMessage(content=template)]
    )


async def generate_blog_article(req: BlogArticleRequest) -> BlogArticleResponse:
    """キーワードからブログ記事を段階的に生成する高水準フロー。"""
    llm = _select_llm_provider(req)

    # 1) 意図の把握（必要に応じて確認質問）
    intent_chain = _intent_prompt(req.language) | llm | StrOutputParser()
    intent_raw = await intent_chain.ainvoke(
        {
            "keyword": req.keyword,
            "audience": req.target_audience or "未指定",
            "style": req.writing_style or "未指定",
        }
    )

    # 軽量JSONパース（LLM出力のゆらぎを吸収する前提で安全に）
    import json as _json

    def safe_json_loads(text: str):
        try:
            return _json.loads(text)
        except Exception:
            # フェンス内コードブロックや余計な文言を取り除く簡易処理
            import re

            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return _json.loads(m.group(0))
                except Exception:
                    pass
            return {
                "need_clarification": True,
                "questions": ["目的や読者像について、もう少し詳しく教えてください。"],
            }

    intent_obj = safe_json_loads(intent_raw)

    if intent_obj.get("need_clarification", False) and not req.clarification_answers:
        # 追加質問が必要だが、回答がない場合はここで返す
        questions = intent_obj.get("questions") or [
            "この記事で読者に最も伝えたいメッセージは何ですか？",
            "想定読者の知識レベル（初心者/中級/上級）は？",
            "記事の目的（教育/販促/採用ブランディングなど）は？",
        ]
        return BlogArticleResponse(need_clarification=True, questions=questions)

    # 2) アウトライン作成
    intent_summary = intent_obj.get("intent_summary")
    if req.clarification_answers:
        # 回答を追記してより明確化
        intent_summary = (
            (intent_summary or "") + "\n補足: " + " / ".join(req.clarification_answers)
        )

    outline_chain = _outline_prompt(req.language) | llm | StrOutputParser()
    outline_raw = await outline_chain.ainvoke(
        {"intent_summary": intent_summary, "section_count": req.section_count}
    )
    outline_obj = safe_json_loads(outline_raw)

    # f-string は flake8 F541 を避けるため通常の連結にする
    title = outline_obj.get("title") or (str(req.keyword) + "について知る")
    outline_list: List[str] = outline_obj.get("outline") or []
    if not outline_list:
        # フォールバックでざっくり4つ作る
        kw = str(req.keyword)
        outline_list = [
            kw + "とは",
            kw + "の基本",
            "実践: " + kw,
            "まとめと次の一歩",
        ]

    # 3) 各セクションを執筆（厳格なプロンプトを付与して逸脱抑止）
    section_prompt = _section_prompt(req.language)
    sections: List[BlogSection] = []
    for h in outline_list[: req.section_count]:
        section_chain = section_prompt | llm | StrOutputParser()
        section_text = await section_chain.ainvoke(
            {
                "title": title,
                "section_title": h,
                "audience": req.target_audience or "一般読者",
                "style": req.writing_style or "フラットで丁寧",
                "keyword": req.keyword,
            }
        )
        sections.append(BlogSection(title=h, content=section_text))

    # 4) Self-Refine (CRITIC) によるトピック整合性の自動チェック＆リライト
    sections_text_parts: List[str] = []
    for s in sections:
        sections_text_parts.append("## " + s.title + "\n\n" + s.content)
    sections_text = "\n\n".join(sections_text_parts)
    critic = _critic_prompt(req.language) | llm | StrOutputParser()
    critique_raw = await critic.ainvoke(
        {
            "keyword": req.keyword,
            "audience": req.target_audience or "一般読者",
            "content": sections_text,
        }
    )
    try:
        critique = _json.loads(critique_raw)
    except Exception:
        critique = {"ok": True, "issues": [], "suggestion": ""}

    if not critique.get("ok", True):
        refine = _refine_prompt(req.language) | llm | StrOutputParser()
        refined_sections_text = await refine.ainvoke(
            {
                "keyword": req.keyword,
                "audience": req.target_audience or "一般読者",
                "issues": "\n".join(critique.get("issues", []))
                + "\n"
                + (critique.get("suggestion") or ""),
                "content": sections_text,
            }
        )
        sections_text = refined_sections_text

    # 編集者視点で全体を校正（最終整形）。逸脱防止の制約を再度付与
    editor_chain = _editor_prompt(req.language) | llm | StrOutputParser()
    final_article = await editor_chain.ainvoke(
        {"title": title, "sections_text": sections_text, "keyword": req.keyword}
    )

    return BlogArticleResponse(
        need_clarification=False,
        title=title,
        outline=outline_list[: req.section_count],
        sections=sections,
        final_article=final_article,
    )
