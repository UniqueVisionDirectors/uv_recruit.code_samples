import { withMermaid } from "vitepress-plugin-mermaid";

export default withMermaid({
  title: "ユーザーID発行API 教材",
  description: "衝突を体験しながら学ぶ分散ID設計チュートリアル",
  themeConfig: {
    sidebar: [
      { text: "01 イントロ / Web構成", link: "/01-intro" },
      { text: "02 環境立ち上げ", link: "/02-setup" },
      { text: "03 APIに触れる", link: "/03-api" },
      { text: "04 ステージ1", link: "/04-stage1" },
      { text: "05 衝突を観測", link: "/05-collision" },
      { text: "06 ステージ2", link: "/06-stage2" },
      { text: "07 付録", link: "/07-appendix" },
    ],
  },
  mermaid: {},
});
