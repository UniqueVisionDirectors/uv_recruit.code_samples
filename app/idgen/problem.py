class ProblemIssuer:
    """出題用スタブ。学習者は `issue` を実装してユーザーIDを返す。

    要件（詳細は docs/superpowers/specs の設計書を参照）:
      - base62（0-9A-Za-z）10文字。
      - 発行順に文字列ソート可能（先頭に時刻成分）。
      - 連番を避ける程度の予測困難性。
      - ステージ2では、並列化（複数コンテナ）でも衝突しないようにする。
        ヒント: プロセス毎に distinct な worker-id を設定 `WORKER_ID` から受け取る。
    """

    def issue(self) -> str:
        raise NotImplementedError("ここにID発行ロジックを実装してください")
