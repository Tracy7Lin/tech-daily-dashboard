from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class OpsStatusAnalysisOutput:
    current_issues: list[dict]
    high_priority: list[dict]
    recently_recovered: list[dict]
    operator_brief: str

    def to_dict(self) -> dict:
        return asdict(self)


class OpsStatusAnalysisCapability:
    def analyze(self, snapshot: dict) -> OpsStatusAnalysisOutput:
        current_issues = snapshot.get("recent_runtime_diagnostics", [])
        high_priority = snapshot.get("high_priority_runtime_issues", [])
        recently_recovered = snapshot.get("recently_recovered_runtime_issues", [])
        return OpsStatusAnalysisOutput(
            current_issues=current_issues,
            high_priority=high_priority,
            recently_recovered=recently_recovered,
            operator_brief=self._build_operator_brief(current_issues, high_priority, recently_recovered),
        )

    def _build_operator_brief(
        self,
        current_issues: list[dict],
        high_priority: list[dict],
        recently_recovered: list[dict],
    ) -> str:
        parts: list[str] = []
        if high_priority:
            companies = "、".join(item["company_slug"] for item in high_priority[:3])
            parts.append(f"当前优先处理 {companies}")
        elif current_issues:
            companies = "、".join(item["company_slug"] for item in current_issues[:3])
            parts.append(f"当前需关注 {companies}")
        else:
            parts.append("当前没有高优先级信源异常")

        if recently_recovered:
            companies = "、".join(item["company_slug"] for item in recently_recovered[:3])
            parts.append(f"最近已恢复 {companies}")
        return "；".join(parts) + "。"
