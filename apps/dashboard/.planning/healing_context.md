# 🚨 Self-Healing Diagnostics Context

The command `npx eslint . --ext .ts,.tsx --max-warnings 0` failed with exit code 1 on 2026-06-20 21:00:39.

## 🔍 Critical Errors & Traces
```text
   98:18  warning  'error' is defined but never used  @typescript-eslint/no-unused-vars
   98:18  warning  'error' is defined but never used  unused-imports/no-unused-vars
  149:18  warning  'error' is defined but never used  @typescript-eslint/no-unused-vars
  149:18  warning  'error' is defined but never used  unused-imports/no-unused-vars
✖ 800 problems (0 errors, 800 warnings)
  0 errors and 267 warnings potentially fixable with the `--fix` option.
```

## 📋 Full Execution Output
```text

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/admin/audits/page.tsx
   77:34  warning  Unexpected any. Specify a different type                                                                      @typescript-eslint/no-explicit-any
   90:8   warning  React Hook useEffect has a missing dependency: 'fetchData'. Either include it or remove the dependency array  react-hooks/exhaustive-deps
   98:65  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      @typescript-eslint/no-unused-vars
   98:65  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      unused-imports/no-unused-vars
  122:61  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      @typescript-eslint/no-unused-vars
  122:61  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      unused-imports/no-unused-vars
  146:58  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      @typescript-eslint/no-unused-vars
  146:58  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                      unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/agent/page.tsx
   77:44  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   84:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   84:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   84:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  135:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  135:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  135:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/analytics/ab-testing/page.tsx
   45:50  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   58:59  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   58:59  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
   61:62  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   61:62  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
   74:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   74:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   74:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  102:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  102:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  102:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  130:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  130:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  130:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/analytics/page.tsx
  47:32  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
  48:30  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
  49:35  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/creation/components/CreationContent.tsx
   76:47  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   76:47  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  105:32  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  105:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  105:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  147:54  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  153:36  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  153:44  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  153:44  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  166:30  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/creation/components/EnhancementPanel.tsx
   3:27  warning  'useRef' is defined but never used. Allowed unused vars must match /^_/u       @typescript-eslint/no-unused-vars
   3:27  warning  'useRef' is defined but never used                                             unused-imports/no-unused-imports
   3:35  warning  'useEffect' is defined but never used. Allowed unused vars must match /^_/u    @typescript-eslint/no-unused-vars
   3:35  warning  'useEffect' is defined but never used                                          unused-imports/no-unused-imports
  16:5   warning  'ChevronDown' is defined but never used. Allowed unused vars must match /^_/u  @typescript-eslint/no-unused-vars
  16:5   warning  'ChevronDown' is defined but never used                                        unused-imports/no-unused-imports

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/creation/components/JobItem.tsx
  6:50  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/creation/components/ScriptEnginePanel.tsx
  49:47  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  49:47  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/creation/components/VisualCorePanel.tsx
   53:38  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   96:25  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  222:29  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  228:36  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  228:42  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  228:42  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/credits/page.tsx
   53:41  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   55:55  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   56:46  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
  105:33  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  105:33  warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  112:35  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/dashboard/experiments/page.tsx
   26:52  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   27:58  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   46:30  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   52:30  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   89:18  warning  'err' is defined but never used           @typescript-eslint/no-unused-vars
   89:18  warning  'err' is defined but never used           unused-imports/no-unused-vars
  113:18  warning  'err' is defined but never used           @typescript-eslint/no-unused-vars
  113:18  warning  'err' is defined but never used           unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/dashboard/intelligence/page.tsx
   25:60  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   31:50  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   54:23  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
   84:18  warning  'err' is defined but never used           @typescript-eslint/no-unused-vars
   84:18  warning  'err' is defined but never used           unused-imports/no-unused-vars
   84:23  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
  317:30  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/dashboard/page.tsx
    5:8   warning  'Link' is defined but never used. Allowed unused vars must match /^_/u                    @typescript-eslint/no-unused-vars
    5:8   warning  'Link' is defined but never used                                                          unused-imports/no-unused-imports
    8:3   warning  'TrendingUp' is defined but never used. Allowed unused vars must match /^_/u              @typescript-eslint/no-unused-vars
    8:3   warning  'TrendingUp' is defined but never used                                                    unused-imports/no-unused-imports
   11:3   warning  'CheckCircle2' is defined but never used. Allowed unused vars must match /^_/u            @typescript-eslint/no-unused-vars
   11:3   warning  'CheckCircle2' is defined but never used                                                  unused-imports/no-unused-imports
   15:3   warning  'Workflow' is defined but never used. Allowed unused vars must match /^_/u                @typescript-eslint/no-unused-vars
   15:3   warning  'Workflow' is defined but never used                                                      unused-imports/no-unused-imports
   17:3   warning  'Database' is defined but never used. Allowed unused vars must match /^_/u                @typescript-eslint/no-unused-vars
   17:3   warning  'Database' is defined but never used                                                      unused-imports/no-unused-imports
   18:3   warning  'Radar' is defined but never used. Allowed unused vars must match /^_/u                   @typescript-eslint/no-unused-vars
   18:3   warning  'Radar' is defined but never used                                                         unused-imports/no-unused-imports
   19:3   warning  'Target' is defined but never used. Allowed unused vars must match /^_/u                  @typescript-eslint/no-unused-vars
   19:3   warning  'Target' is defined but never used                                                        unused-imports/no-unused-imports
   20:3   warning  'ShieldCheck' is defined but never used. Allowed unused vars must match /^_/u             @typescript-eslint/no-unused-vars
   20:3   warning  'ShieldCheck' is defined but never used                                                   unused-imports/no-unused-imports
   21:3   warning  'LineChart' is defined but never used. Allowed unused vars must match /^_/u               @typescript-eslint/no-unused-vars
   21:3   warning  'LineChart' is defined but never used                                                     unused-imports/no-unused-imports
   22:3   warning  'ArrowUpRight' is defined but never used. Allowed unused vars must match /^_/u            @typescript-eslint/no-unused-vars
   22:3   warning  'ArrowUpRight' is defined but never used                                                  unused-imports/no-unused-imports
   27:20  warning  'WS_BASE' is defined but never used. Allowed unused vars must match /^_/u                 @typescript-eslint/no-unused-vars
   27:20  warning  'WS_BASE' is defined but never used                                                       unused-imports/no-unused-imports
   30:23  warning  'AssetQuickview' is defined but never used. Allowed unused vars must match /^_/u          @typescript-eslint/no-unused-vars
   30:23  warning  'AssetQuickview' is defined but never used                                                unused-imports/no-unused-imports
   32:10  warning  'Button' is defined but never used. Allowed unused vars must match /^_/u                  @typescript-eslint/no-unused-vars
   32:10  warning  'Button' is defined but never used                                                        unused-imports/no-unused-imports
   44:52  warning  Unexpected any. Specify a different type                                                  @typescript-eslint/no-explicit-any
   45:22  warning  'setActionLogs' is assigned a value but never used. Allowed unused vars must match /^_/u  @typescript-eslint/no-unused-vars
   45:22  warning  'setActionLogs' is assigned a value but never used. Allowed unused vars must match /^_/u  unused-imports/no-unused-vars
   52:28  warning  Unexpected any. Specify a different type                                                  @typescript-eslint/no-explicit-any
   52:36  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                  @typescript-eslint/no-unused-vars
   52:36  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                  unused-imports/no-unused-vars
   62:26  warning  Unexpected any. Specify a different type                                                  @typescript-eslint/no-explicit-any
  279:63  warning  Unexpected any. Specify a different type                                                  @typescript-eslint/no-explicit-any
  328:76  warning  Unexpected any. Specify a different type                                                  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/dashboard/video-editor/page.tsx
   46:42  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
   57:32  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
   57:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                 @typescript-eslint/no-unused-vars
   57:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                 unused-imports/no-unused-vars
   87:32  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
   87:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                 @typescript-eslint/no-unused-vars
   87:38  warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                 unused-imports/no-unused-vars
  104:29  warning  'data' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                   @typescript-eslint/no-unused-vars
  104:29  warning  'data' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                                                   unused-imports/no-unused-vars
  206:66  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
  234:37  warning  Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/dev/analysis-card/page.tsx
  127:36  warning  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/discovery/components/AnalysisPanel.tsx
    8:5   warning  'Globe' is defined but never used. Allowed unused vars must match /^_/u                 @typescript-eslint/no-unused-vars
    8:5   warning  'Globe' is defined but never used                                                       unused-imports/no-unused-imports
    9:5   warning  'Loader2' is defined but never used. Allowed unused vars must match /^_/u               @typescript-eslint/no-unused-vars
    9:5   warning  'Loader2' is defined but never used                                                     unused-imports/no-unused-imports
   10:5   warning  'XCircle' is defined but never used. Allowed unused vars must match /^_/u               @typescript-eslint/no-unused-vars
   10:5   warning  'XCircle' is defined but never used                                                     unused-imports/no-unused-imports
   24:14  warning  Unexpected any. Specify a different type                                                @typescript-eslint/no-explicit-any
   85:5   warning  Prop 'activeEngine' should be read-only                                                 react/prefer-read-only-props
   86:5   warning  Prop 'intelData' should be read-only                                                    react/prefer-read-only-props
   87:5   warning  Prop 'networkData' should be read-only                                                  react/prefer-read-only-props
   88:5   warning  Prop 'alerts' should be read-only                                                       react/prefer-read-only-props
   89:5   warning  Prop 'displayLogs' should be read-only                                                  react/prefer-read-only-props
   90:5   warning  Prop 'mapPoints' should be read-only                                                    react/prefer-read-only-props
   91:5   warning  Prop 'activeNiche' should be read-only                                                  react/prefer-read-only-props
   92:5   warning  Prop 'onCreateFromAnalysis' should be read-only                                         react/prefer-read-only-props
   93:5   warning  Prop 'analysisTasks' should be read-only                                                react/prefer-read-only-props
  104:5   warning  'onCreateFromAnalysis' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  104:5   warning  'onCreateFromAnalysis' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  105:5   warning  'analysisTasks' is defined but never used. Allowed unused args must match /^_/u         @typescript-eslint/no-unused-vars
  105:5   warning  'analysisTasks' is defined but never used. Allowed unused args must match /^_/u         unused-imports/no-unused-vars
  126:61  warning  Unexpected any. Specify a different type                                                @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/discovery/components/CandidateCard.tsx
  11:5  warning  Prop 'candidate' should be read-only      react/prefer-read-only-props
  12:5  warning  Prop 'credits' should be read-only        react/prefer-read-only-props
  13:5  warning  Prop 'onAnalyze' should be read-only      react/prefer-read-only-props
  14:5  warning  Prop 'onRemove' should be read-only       react/prefer-read-only-props
  15:5  warning  Prop 'onCreateVideo' should be read-only  react/prefer-read-only-props

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/discovery/components/CandidateGrid.tsx
  10:5  warning  Prop 'candidates' should be read-only         react/prefer-read-only-props
  11:5  warning  Prop 'isScanning' should be read-only         react/prefer-read-only-props
  12:5  warning  Prop 'isKeywordSearch' should be read-only    react/prefer-read-only-props
  13:5  warning  Prop 'activeNiche' should be read-only        react/prefer-read-only-props
  14:5  warning  Prop 'credits' should be read-only            react/prefer-read-only-props
  15:5  warning  Prop 'onAnalyze' should be read-only          react/prefer-read-only-props
  16:5  warning  Prop 'onRemoveCandidate' should be read-only  react/prefer-read-only-props
  17:5  warning  Prop 'onCreateVideo' should be read-only      react/prefer-read-only-props

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/discovery/components/DiscoveryContent.tsx
   57:42   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
   58:48   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
   59:115  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
   70:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
   70:38   warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                               @typescript-eslint/no-unused-vars
   70:38   warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                               unused-imports/no-unused-vars
  147:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
  147:38   warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                               @typescript-eslint/no-unused-vars
  147:38   warning  'signal' is defined but never used. Allowed unused args must match /^_/u                                                                                                                                                                                               unused-imports/no-unused-vars
  174:39   warning  The ref value 'pollingRefs.current' will likely have changed by the time this effect cleanup function runs. If this ref points to a node rendered by React, copy 'pollingRefs.current' to a variable inside the effect, and use that variable in the cleanup function  react-hooks/exhaustive-deps
  202:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
  251:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
  282:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any
  299:32   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                               @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/discovery/components/DiscoveryHeader.tsx
  12:14  warning  Unexpected any. Specify a different type          @typescript-eslint/no-explicit-any
  17:5   warning  Prop 'activeNiche' should be read-only            react/prefer-read-only-props
  18:5   warning  Prop 'onNicheChange' should be read-only          react/prefer-read-only-props
  19:5   warning  Prop 'isKeywordSearch' should be read-only        react/prefer-read-only-props
  20:5   warning  Prop 'onKeywordSearchChange' should be read-only  react/prefer-read-only-props
  21:5   warning  Prop 'activeRegion' should be read-only           react/prefer-read-only-props
  22:5   warning  Prop 'onRegionChange' should be read-only         react/prefer-read-only-props
  23:5   warning  Prop 'isScanning' should be read-only             react/prefer-read-only-props
  24:5   warning  Prop 'onScan' should be read-only                 react/prefer-read-only-props
  25:5   warning  Prop 'analysisTasks' should be read-only          react/prefer-read-only-props
  26:5   warning  Prop 'onCreateFromAnalysis' should be read-only   react/prefer-read-only-props

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/knowledge/page.tsx
   43:15   warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any
   68:56   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
   68:56   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
   96:18   warning  'e' is defined but never used                                             @typescript-eslint/no-unused-vars
   96:18   warning  'e' is defined but never used                                             unused-imports/no-unused-vars
  102:33   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  102:33   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  133:49   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  @typescript-eslint/no-unused-vars
  133:49   warning  'signal' is defined but never used. Allowed unused args must match /^_/u  unused-imports/no-unused-vars
  387:115  warning  Unexpected any. Specify a different type                                  @typescript-eslint/no-explicit-any

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/login/page.tsx
   92:26  warning  'loginErr' is defined but never used  @typescript-eslint/no-unused-vars
   92:26  warning  'loginErr' is defined but never used  unused-imports/no-unused-vars
  100:18  warning  'err' is defined but never used       @typescript-eslint/no-unused-vars
  100:18  warning  'err' is defined but never used       unused-imports/no-unused-vars

/home/psalmprax/ALL_PROJECTS/ettametta/apps/dashboard/src/app/nexus/components/NexusContent.tsx
  118:20   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
  118:28   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
  125:111  warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
  236:53   warning  Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
  544:61   warning  Unexpected any. Specify a different type                                                                                                                                                                                                                                                 @typescript-eslint/no-explicit-any
```

---
*Created automatically by agent-helper heal.*
