import { withMermaid } from "vitepress-plugin-mermaid";

export default withMermaid({
  lang: "ja-JP",
  title: "ユーザーID発行API サンプル",
  description: "衝突を体験しながら学ぶ分散ID設計チュートリアル",
  // サンプルは手元の localhost サービスを案内するため、到達性チェックの対象外にする。
  ignoreDeadLinks: [/^https?:\/\/localhost/],
  themeConfig: {
    // 上部ナビ：どのページからでもホーム／チュートリアル先頭へ戻れる。
    nav: [
      { text: "ホーム", link: "/" },
      { text: "チュートリアル", link: "/01-web-basics" },
    ],
    // 左サイドバー：doc レイアウトの各ページで常時表示。前後リンクもこの順序から生成される。
    sidebar: [
      {
        text: "チュートリアル",
        items: [
          { text: "01 Webアプリの基本構成", link: "/01-web-basics" },
          { text: "02 サンプルの構成と起動", link: "/02-stack-setup" },
          { text: "03【問題①】ID発行を実装", link: "/03-exercise-issue" },
          { text: "04【解答例①】実装の解説", link: "/04-solution-issue" },
          { text: "05 スケールとロードバランサー", link: "/05-scale-lb" },
          { text: "06【問題②】衝突を観測", link: "/06-exercise-collision" },
          { text: "07【解答例②】worker-id 設計", link: "/07-solution-workerid" },
        ],
      },
    ],
    docFooter: { prev: "前へ", next: "次へ" },
    outline: { label: "このページの目次", level: [2, 3] },
    darkModeSwitchLabel: "外観",
    lightModeSwitchTitle: "ライトモードに切り替え",
    darkModeSwitchTitle: "ダークモードに切り替え",
    sidebarMenuLabel: "メニュー",
    returnToTopLabel: "トップへ戻る",
  },
  mermaid: {
    // 図をコンテナ幅に縮小せず自然サイズで表示し、小さくなりすぎないようにする。
    // はみ出す場合はテーマ CSS（.mermaid に overflow-x:auto）で横スクロールにする。
    flowchart: { useMaxWidth: false, htmlLabels: true },
    sequence: { useMaxWidth: false },
    // 図中の文字を大きめにする（既定 ~16px → 21px ≒ 1.3倍）。レイアウト段階で
    // 反映されるためノードもそれに合わせて大きくなる。
    themeVariables: { fontSize: "21px" },
  },
});
