import { withMermaid } from "vitepress-plugin-mermaid";

export default withMermaid({
  lang: "ja-JP",
  title: "ユーザーID発行API 教材",
  description: "衝突を体験しながら学ぶ分散ID設計チュートリアル",
  themeConfig: {
    // 上部ナビ：どのページからでもホーム／チュートリアル先頭へ戻れる。
    nav: [
      { text: "ホーム", link: "/" },
      { text: "チュートリアル", link: "/01-intro" },
    ],
    // 左サイドバー：doc レイアウトの各ページで常時表示。前後リンクもこの順序から生成される。
    sidebar: [
      {
        text: "チュートリアル",
        items: [
          { text: "01 イントロ / Web構成", link: "/01-intro" },
          { text: "02 環境を立ち上げる", link: "/02-setup" },
          { text: "03 APIに触れる", link: "/03-api" },
          { text: "04 ステージ1（穴埋め）", link: "/04-stage1" },
          { text: "05 衝突を観測する", link: "/05-collision" },
          { text: "06 ステージ2（解決）", link: "/06-stage2" },
          { text: "07 付録", link: "/07-appendix" },
        ],
      },
    ],
    // 下部の前後ページリンク（日本語ラベル）。
    docFooter: { prev: "前へ", next: "次へ" },
    // 右側の見出し目次。
    outline: { label: "このページの目次", level: [2, 3] },
    // 各種 UI ラベルの日本語化。
    darkModeSwitchLabel: "外観",
    lightModeSwitchTitle: "ライトモードに切り替え",
    darkModeSwitchTitle: "ダークモードに切り替え",
    sidebarMenuLabel: "メニュー",
    returnToTopLabel: "トップへ戻る",
  },
  mermaid: {},
});
