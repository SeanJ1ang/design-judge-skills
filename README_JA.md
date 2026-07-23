<div align="center">

<img src="assets/readme-banner-en.png" alt="Design Judge Skills バナー" width="100%">

# Design Judge Skills

デザインアワードの一連のワークフローを支援する、エビデンス重視の Agent Skills：受賞事例の調査、デザイン評価、アワードのマッチング、応募文の作成、最終提出レビューに対応します。

[![License](https://img.shields.io/badge/license-Apache--2.0-2ea44f)](LICENSE)
[![Install](https://img.shields.io/badge/install-Claude%20Code%20%7C%20Codex%20%7C%20OpenClaw%20%7C%20OpenCode%20%7C%20Hermes-111827)](#5-インストール)
[![Skills](https://img.shields.io/badge/skills-6-0ea5e9)](#6-スキル一覧)
[![Observed Works](https://img.shields.io/badge/observed%20works-22%2C125-7c3aed)](docs/benchmark-coverage_EN.md)
[![Language](https://img.shields.io/badge/language-%E4%B8%AD%E6%96%87%20%7C%20English%20%7C%20%E6%97%A5%E6%9C%AC%E8%AA%9E-1f6feb)](README.md)

[クイックスタート](#4-クイックスタート) · [ベンチマークの範囲](docs/benchmark-coverage_EN.md) · [インストール](#5-インストール) · [スキル一覧](#6-スキル一覧) · [コントリビューション](#7-コントリビューションと開発) · [Star 履歴](#8-star-履歴) · [中文](README.md) · [English](README_EN.md)

</div>

`design-judge-skills` は、デザインアワードへの応募プロセスを、境界が明確で個別に呼び出し・検証できるスキルモジュールとして構成します。公式情報源、エビデンスの参照箇所、透明性のある採点に基づいて追跡可能な意思決定を支援し、公開された基準を用いて応募経路を比較し、適合度を説明して優先順位を決定します。

## 目次

- [1. プロジェクト概要](#1-プロジェクト概要)
- [2. ワークフロー](#2-ワークフロー)
- [3. 設計原則と境界](#3-設計原則と境界)
- [4. クイックスタート](#4-クイックスタート)
- [5. インストール](#5-インストール)
  - [5.1 npx skills でインストール](#51-npx-skills-でインストール)
  - [5.2 Claude Code](#52-claude-code)
  - [5.3 Codex](#53-codex)
  - [5.4 その他の Agent](#54-その他の-agent)
- [6. スキル一覧](#6-スキル一覧)
- [7. コントリビューションと開発](#7-コントリビューションと開発)
- [8. Star 履歴](#8-star-履歴)

## 1. プロジェクト概要

Design Judge Skills は、デザインアワード応募ワークフローの中核となる次の 5 つのタスクに対応します。

- 同じ機能カテゴリーの受賞事例を検索し、検証する。
- エビデンスに基づくルーブリックで、デザインの品質とプレゼンテーションを評価する。
- プロジェクトに適したアワード、プログラム、部門、応募カテゴリーを照合する。
- ユーザーが提供したプロジェクト資料から、根拠に基づく応募文を作成する。
- 現行の公式規則に照らして、提出パッケージを監査する。

現在の設定は、iF DESIGN AWARD、iF DESIGN STUDENT AWARD、Red Dot Product Design、Red Dot Design Concept、IDEA、DIA、K-Design、GOOD DESIGN AWARD Japan、Core77、James Dyson、EPDA に対応しています。締切、料金、応募資格の対象期間、カテゴリー、提出仕様は、実行時に公式ページで再確認する必要があります。

評価モジュールには、iF、iF Student、Red Dot、IDEA の受賞作または選出作から集約した **22,125 件の観察データ**が含まれます。これらは説明のための背景情報のみを提供するもので、基本スコアを変更せず、受賞確率の推定にも使用できません。詳しくは[対象範囲、プライバシー、制限事項](docs/benchmark-coverage_EN.md)を参照してください。

## 2. ワークフロー

```text
デザイン資料 ── 経路が未確定、または全工程が必要 ──> design-award-pipeline
  │
  ├─ 類似する受賞作を探す ────────────────> design-award-search
  ├─ デザインとプレゼンテーションを評価 ──> design-evaluation
  └─ アワード / プログラム / カテゴリーを選択 ──> design-award-match
                                                    │
                                                    v
                                           design-information-prep
                                                    │
                                                    v
                                           design-submission-check
```

各モジュールは個別に使用できます。完全な応募ワークフローは通常、評価またはアワードのマッチングから始まり、応募先が確定したら情報準備へ進み、最後に提出準備状況を監査します。

## 3. 設計原則と境界

1. **一次情報を優先する。** アワード規則と受賞作のエビデンスは公式ページから取得します。検索結果の抜粋や第三者ページは、手がかりを見つける目的にのみ使用します。
2. **事実と推論を分ける。** ユーザー資料に含まれる事実、モデルによる推論、ユーザーの確認を待つ項目を明確に区別します。
3. **採点の透明性を保つ。** 評価スコアと適合度スコアは意思決定を支援するものであり、受賞確率を示すものではありません。
4. **各モジュールの責務を 1 つにする。** 検索、評価、アワードのマッチング、応募文の作成、提出レビューが、暗黙のうちに互いの役割を置き換えることはありません。
5. **公式審査員を装わない。** 公開済みの審査基準に合わせることはできますが、非公開の審査員の好みや内部プロセスを捏造してはなりません。

## 4. クイックスタート

インストール後、デザイン画像、ボード、マニュアル、プロジェクト概要、調査資料、応募ファイルを Agent に渡し、タスクを指定します。以下のプロンプトはそのままコピーできます。

| 目的 | プロンプト例 |
|---|---|
| 全工程を計画する | `Use $design-award-pipeline to plan the complete award route from these materials and maintain a handoff across stages.` |
| 類似する受賞作を探す | `Use $design-award-search to find officially verified award winners in the same category as this rehabilitation product.` |
| 学生コンセプトを評価する | `Use $design-evaluation to evaluate the attached design. I define its maturity as Student Concept. Report design quality, presentation quality, evidence confidence, and Critical issues separately.` |
| 応募先候補を比較する | `Use $design-award-match to compare iF Student, Red Dot Design Concept, DIA, Core77, and James Dyson for this project.` |
| 応募文を準備する | `Use $design-information-prep to prepare an IDEA entry from the attached material. List missing facts first, then draft each English field and check its word count.` |
| 最終監査を実行する | `Use $design-submission-check to audit this package against the current official rules and return a go, conditional go, or no-go decision.` |

どのスキルを使うべきか分からない場合は、`design-award-pipeline` を呼び出してください。全工程を強制するのではなく、必要最小限のモジュールだけを選択します。

## 5. インストール

各 `skills/<name>/` ディレクトリは、個別にインストールできる単位です。`design-judge-shared` はサポートパッケージです。すべてをインストールする場合は自動的に含まれますが、`design-award-search` または `design-award-match` だけをインストールする場合は、共有パッケージも一緒にインストールしてください。

### 5.1 `npx skills` でインストール

[Node.js 18 以降](https://nodejs.org/)が必要です。CLI をグローバルにインストールする必要はありません。

利用可能なスキルを一覧表示します。

```bash
npx skills add SeanJ1ang/design-judge-skills --list
```

すべてのスキルを Codex 用としてグローバルにインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --global --agent codex --skill '*' --yes --copy
```

独立したスキルを 1 つ、現在のプロジェクトにインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --agent codex --skill design-evaluation --yes --copy
```

共有パッケージに依存するスキルをインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --global --agent codex \
  --skill design-award-search --skill design-judge-shared --yes --copy
```

対応するすべての Agent にコレクションをインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --all
```

インストール済みスキルの確認と更新を行います。

```bash
npx skills list --global --agent codex
npx skills update --global --yes
```

### 5.2 Claude Code

コレクション全体をインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --global --agent claude-code --skill '*' --yes --copy
```

インストール後に新しい Claude Code セッションを開始し、タスクを自然言語で説明するか、スキル名を明示します。

```text
Use $design-award-match to compare the best award routes for this student concept.
```

### 5.3 Codex

コレクションを Codex のグローバルスキルディレクトリにインストールします。

```bash
npx skills add SeanJ1ang/design-judge-skills --global --agent codex --skill '*' --yes --copy
```

リポジトリを Codex に直接指定することもできます。

```text
Install all Codex skills from https://github.com/SeanJ1ang/design-judge-skills.
Preserve every complete skill directory and install design-judge-shared as well.
Validate the frontmatter of every SKILL.md after installation.
```

インストールまたは更新後、新しい Codex セッションを開始し、スキル一覧を完全に更新してください。

### 5.4 その他の Agent

OpenClaw、OpenCode、Hermes Agent、Cursor、Cline、Gemini CLI など、`npx skills` が対応する Agent は、それぞれの `--agent` 識別子で指定できます。例：

```bash
npx skills add SeanJ1ang/design-judge-skills --global --skill '*' --yes --copy \
  --agent openclaw --agent opencode --agent hermes-agent
```

対応するすべての Agent にインストールするには、次を実行します。

```bash
npx skills add SeanJ1ang/design-judge-skills --all
```

`SKILL.md` に対応するその他の Agent では、次の手順を実行します。

1. このリポジトリを安定したパスに clone します。
2. 完全な各スキルディレクトリを Agent のスキルディレクトリへコピーするか、リンクします。
3. `SKILL.md`、`agents/`、`references/`、`scripts/`、`examples/`、`tests/` を維持します。
4. `design-award-search` および `design-award-match` とともに `design-judge-shared` を配置します。

## 6. スキル一覧

| スキル | 状態 | 目的 | 代表的なトリガー |
|---|---|---|---|
| [`design-award-pipeline`](skills/design-award-pipeline/README_EN.md) | Beta | 不確定または複数段階にまたがる依頼に対して、必要最小限の経路を選択し、段階間の引き継ぎを維持する | 「全応募プロセス」「次に何をすべきか」「award pipeline」 |
| [`design-award-search`](skills/design-award-search/README_EN.md) | Stable | 公式情報源から同じカテゴリーの受賞作を検索し、検証する | 「同カテゴリーの受賞作」「award winners」「design benchmarks」 |
| [`design-evaluation`](skills/design-evaluation/README_EN.md) | Beta | ユーザーが選択した成熟度区分に基づき、エビデンスの信頼度と Critical リスクを含めてデザインとプレゼンテーションを評価する | 「デザインを評価」「採点」「critique」「batch evaluate」 |
| [`design-award-match`](skills/design-award-match/README_EN.md) | Beta | アワード、プログラム、部門、カテゴリーを照合し、構造的な応募資格と応募優先度を確認する | 「どのアワードに応募すべきか」「アワードのマッチング」「award fit」 |
| [`design-information-prep`](skills/design-information-prep/README_EN.md) | Beta | ユーザー資料からプロジェクトの事実を抽出し、必要な応募項目を準備する | 「応募文を準備」「entry writing」「project dossier」 |
| [`design-submission-check`](skills/design-submission-check/README_EN.md) | Beta | 現行の公式規則に基づいて、完全性、一貫性、権利上のリスク、準備状況を監査する | 「提出前チェック」「compliance review」「go/no-go」 |
| [`design-judge-shared`](skills/design-judge-shared/SKILL.md) | Support | 検索スキルとマッチングスキルが使用する共有分類体系と公式情報源の規則を提供する。単独のワークフローではない | インストール時の依存パッケージ |

`Beta` は、スキルがサンプルと自動テストで検証されているものの、まだエッジケースが存在する可能性があることを示します。`Stable` は、ワークフローと規則が比較的成熟していることを示します。`Support` は、他のスキルからのみ使用されるパッケージを表します。バッジの数はユーザー向けの 6 つのワークフローを示し、共有サポートパッケージは含みません。

## 7. コントリビューションと開発

### 7.1 リポジトリ構成

```text
skills/
├── design-judge-shared/
│   ├── SKILL.md
│   ├── category-taxonomy.md
│   └── source-registry.md
└── design-<topic>/
    ├── SKILL.md
    ├── README.md
    ├── README_EN.md
    ├── agents/openai.yaml
    ├── references/
    ├── scripts/
    ├── examples/
    └── tests/
```

### 7.2 開発規則

- スキルディレクトリ名を frontmatter の `name` と一致させ、小文字、数字、ハイフンのみを使用します。
- `description` には、スキルの機能、呼び出すべき状況、使用すべきでない状況を記述します。
- 中核ワークフローは `SKILL.md` に置き、長い規則、仕様、スキーマは `references/` に移します。
- 反復可能で決定論的な処理は `scripts/` に置き、テストで検証します。
- ユーザー向けの各スキルに、入力、出力、境界、関連スキルを説明する、章構成を揃えた中国語と英語の詳細ページを用意します。
- 現在の締切、料金、応募資格の対象期間、提出仕様を、長期的に不変の事実としてハードコードしないでください。実行時に公式情報源で検証します。
- API キー、Cookie、ログインセッション、ユーザーのプロジェクト資料、非公開の受賞作データベース、著作権で保護された事例全文をコミットしないでください。

### 7.3 スキルの追加または更新

1. `skills/design-<topic>/` に完全なディレクトリを作成するか、既存のディレクトリを更新します。
2. 有効な `SKILL.md` frontmatter と簡潔なワークフローを記述します。
3. 必要な UI メタデータ、参考資料、スクリプト、サンプル、テストを追加します。
4. 両方の README にあるスキル一覧、状態ラベル、依存関係の説明を更新します。
5. コミット前に、関連する単体テストと基本的な検証を実行します。

PowerShell ですべての単体テストスイートを実行します。

```powershell
Get-ChildItem skills -Directory | ForEach-Object {
  if (Test-Path (Join-Path $_.FullName 'tests')) {
    Push-Location $_.FullName
    python -B -m unittest discover -s tests -p 'test_*.py' -v
    Pop-Location
  }
}
```

さらに、次を実行します。

```bash
git diff --check
npx skills add . --list
```

規則の変更、失敗事例、互換性の問題を報告する Issue を歓迎します。Pull Request には、エビデンスの情報源、検証方法、影響を受けるスキルを記載してください。

## 8. Star 履歴

[![Star History Chart](assets/star-history.svg)](https://github.com/SeanJ1ang/design-judge-skills/stargazers)

GitHub Actions は公開 Star 数を毎日記録し、数が変化した場合にのみローカルのグラフを更新します。履歴はローカル追跡を有効にした日から蓄積され、第三者の画像サービスや Stargazers ユーザー一覧 API には依存しません。
