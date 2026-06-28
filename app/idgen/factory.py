from app.core.config import Settings
from app.idgen.base import IdIssuer
from app.idgen.generator import UserIdGenerator
from app.idgen.problem import ProblemIssuer


def build_issuer(settings: Settings) -> IdIssuer:
    if settings.id_strategy == "problem":
        return ProblemIssuer()
    if settings.id_strategy == "stage1":
        # 素朴解: worker-id 無し（全プロセス 0）。並列下で衝突する。
        return UserIdGenerator(worker_id=0)
    # stage2: プロセス毎に distinct な worker-id。
    return UserIdGenerator(worker_id=settings.worker_id)
