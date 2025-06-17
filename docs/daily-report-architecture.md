# 每日報告生成：架構概覽 (Architecture Overview)

**版本**: 1.0
**最後更新**: 2025-06-16

## 1. 總覽 (Overview)

本文件旨在說明「Meta-Awareness 自動化報告系統」中，每日報告（Daily Report）生成功能的核心架構。此系統的目標是自動化整個流程：從讀取 Google Sheets 中的原始日誌數據，到呼叫大型語言模型（LLM）進行分析，最終將結構化的報告儲存回表格並透過電子郵件發送。

此架構的設計核心是**模組化**與**關注點分離**，確保系統的每一部分都易於理解、維護和擴展。

## 2. 設計原則 (Core Principles)

我們在設計中遵循了幾個關鍵的軟體工程原則：

### 單一職責原則 (Single Responsibility Principle - SRP)
每個服務（`.js` 檔案）只專注於做好一件事情。
- `EmailService.js` 只處理郵件事務。
- `SheetService.js` 只處理表格的讀寫。
- `ApiService.js` 只處理對外部 API 的呼叫。
這種設計使得程式碼**高內聚**，當需求變更時，我們能精準地知道要去修改哪個檔案。

### 門面模式 (Facade Pattern)
`DailyReportService.js` 作為整個流程的「門面」或「指揮家」。外部世界（例如，一個時間觸發器）只需與這個簡單的門面互動，而無需了解背後各個子系統之間複雜的協調過程。這讓系統的依賴關係變得**低耦合**，且更容易使用。

## 3. 核心元件解析 (Component Breakdown)

*(註：根據您的要求，此處忽略 `Showdown.js` 和 `WeeklyReport.js`)*

- **`Config.js` - 全域設定檔**
  - **職責**: 集中管理整個專案的所有可配置參數。
  - **核心功能**: 提供如 API Key、工作表名稱、模型名稱、郵件主旨範本等全域常數。

- **`DailyReportService.js` - 日報門面服務 (Facade)**
  - **職責**: 作為總指揮，協調其他所有服務來完成「生成一份日報」的完整任務。
  - **核心功能**:
    - `generateReport()`: 整個流程的起始點，依序呼叫其他服務。
    - `_buildDailyPrompt()`: 根據數據和分數，組裝發送給 LLM 的結構化 Prompt。

- **`BehaviorScoreService.js` - 行為分數服務**
  - **職責**: 負責所有與「行為分數」相關的計算邏輯。
  - **核心功能**:
    - `calculateDailyScore()`: 根據當天的行為列表，計算出每日效率分數（DES）。
    - 內部包含從 Google Sheets 讀取分數對照表並快取的邏輯。

- **`SleepQualityService.js` - 睡眠品質服務**
  - **職責**: 負責所有與「睡眠品質」相關的計算邏輯。
  - **核心功能**:
    - `calculateSleepHealthIndex()`: 根據睡眠起訖時間和品質評分，計算出睡眠健康指數。
    - 這是一個純粹的計算模組，沒有外部依賴。

- **`SheetService.js` (建議新增) - 表格服務**
  - **職責**: 封裝所有與 Google Sheets 的**讀寫操作 (I/O)**。
  - **核心功能**:
    - `getDailyEntry()`: 從 `MetaLog` 讀取指定日期的原始數據。
    - `saveReport()`: 將生成的報告寫入 `Daily Report` 工作表，並處理覆蓋邏輯。

- **`ApiService.js` (建議新增) - API 服務**
  - **職責**: 專門處理與第三方 API (例如 DeepSeek) 的所有通訊。
  - **核心功能**:
    - `getAnalysis()`: 呼叫 LLM API，內含請求 JSON 格式、錯誤處理和重試機制。

- **`EmailService.js` (建議新增) - 郵件服務**
  - **職責**: 處理所有與電子郵件相關的事務。
  - **核心功能**:
    - `sendDailyReport()`: 組合並發送日報郵件。
    - `_renderHtmlReport()`: 將結構化的報告 JSON 數據渲染成美觀的 HTML 格式。
    - 內部包含帶有重試機制的郵件發送與 Gmail 標籤應用邏輯。

- **`BehaviorScoreManager.js` - (輔助) 行為分數管理器**
  - **職責**: 這是一個**獨立的輔助工具**，用於從日誌中收集新行為，並使用 LLM 進行評分，以維護 `Behavior Scores` 這張對照表。它不是日報生成流程的直接部分，而是其數據來源的維護工具。

## 4. 執行流程 (Execution Workflow)

當 `runDailyReportGeneration()` 被觸發時，系統的執行順序如下：

1.  **觸發器** 呼叫 `DailyReportService.generateReport()`。
2.  **`DailyReportService`** (指揮家) 開始工作：
3.  它呼叫 **`SheetService`** 去 `MetaLog` 讀取當天的原始日誌。
4.  接著，它將日誌數據分別傳遞給 **`BehaviorScoreService`** 和 **`SleepQualityService`** 來計算分數。
5.  然後，它將原始數據和計算出的分數組合成一個詳細的 **Prompt**。
6.  它呼叫 **`ApiService`**，將 Prompt 發送給 LLM，並獲取一個結構化的 JSON 分析報告。
7.  它再次呼叫 **`SheetService`**，將包含 AI 分析的完整報告儲存到 `Daily Report` 工作表中。
8.  最後，它呼叫 **`EmailService`**，將報告數據渲染成 HTML，並將這封精美的報告郵件發送給使用者。
9.  流程結束。

## 5. 架構流程圖 (Data Flow Diagram)