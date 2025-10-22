# Architecture Diagrams: VSCode Validator v2.3.0

**Документ:** Технические диаграммы и схемы архитектуры
**Связанный PRD:** [PRD_vscode_validator_v2.3.0.md](./PRD_vscode_validator_v2.3.0.md)
**Дата:** 2025-10-05

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "VSCode Integration"
        VSCode[VSCode Editor]
        RunOnSave[Run on Save Extension]
        Tasks[tasks.json]
    end

    subgraph "Validator v2.3.0"
        CLI[CLI Entry Point]
        Pipeline[ValidationPipeline]

        subgraph "Processing Stages"
            Loader[FileLoaderStage]
            FormatDetect[FormatDetectionStage]
            Jinja[Jinja2ProcessingStage]
            Import[ImportResolutionStage]
            Parse[JSONParsingStage]
            PosMap[PositionMappingStage]
            Validate[SDUIValidationStage]
            Format[ErrorFormattingStage]
        end

        subgraph "Support Modules"
            Cache[CacheLayer]
            SourceMap[LayeredSourceMap]
            Context[ContextProvider]
        end
    end

    subgraph "External Dependencies"
        Nunjucks[Nunjucks Engine]
        MCP[alfa-sdui-mcp]
        FileSystem[File System]
    end

    VSCode -->|Save File| RunOnSave
    RunOnSave -->|Execute| Tasks
    Tasks -->|Run| CLI

    CLI --> Pipeline
    Pipeline --> Loader
    Loader --> FormatDetect
    FormatDetect -->|.j2.json| Jinja
    FormatDetect -->|.json| Parse
    Jinja --> Import
    Import --> Parse
    Parse --> PosMap
    PosMap --> Validate
    Validate --> Format
    Format -->|Report| CLI
    CLI -->|Display| VSCode

    Jinja -.->|Use| Nunjucks
    Jinja -.->|Use| Context
    Import -.->|Read| FileSystem
    Import -.->|Use| Cache
    PosMap -.->|Use| SourceMap
    Validate -.->|Call| MCP

    style Jinja fill:#90EE90
    style Import fill:#90EE90
    style PosMap fill:#FFD700
    style SourceMap fill:#FFD700
    style Context fill:#87CEEB
    style Cache fill:#87CEEB
```

---

## 2. Validation Pipeline Flow

```mermaid
flowchart TD
    Start([Input: contract.j2.json]) --> Load[Load File]
    Load --> Detect{Detect Format}

    Detect -->|Pure JSON| FastPath[Fast Path: Direct Parse]
    Detect -->|.j2.json or Jinja2 syntax| Jinja2Path[Jinja2 Processing Path]

    FastPath --> Parse[JSON.parse]

    Jinja2Path --> LoadContext[Load/Generate Context]
    LoadContext --> Render[Render Jinja2 Template]
    Render --> BuildSourceMap1[Build Jinja2 Source Map]
    BuildSourceMap1 --> CheckImports{Has Comment-Imports?}

    CheckImports -->|No| Parse
    CheckImports -->|Yes| ParseImports[Parse Import Declarations]
    ParseImports --> ValidateImports[Validate Import Paths]
    ValidateImports --> CheckCircular{Circular Dependency?}

    CheckCircular -->|Yes| ErrorCircular[ERROR: Circular Dependency]
    CheckCircular -->|No| ResolveImports[Resolve Imports Recursively]
    ResolveImports --> ExpandImports[Expand Imports Inline]
    ExpandImports --> BuildSourceMap2[Build Import Source Map]
    BuildSourceMap2 --> Parse

    Parse --> ParseSuccess{Parse Success?}
    ParseSuccess -->|No| ErrorParse[ERROR: JSON Syntax]
    ParseSuccess -->|Yes| BuildPosMap[Build Position Map]

    BuildPosMap --> LayerSourceMaps[Layer Source Maps]
    LayerSourceMaps --> MCPValidate[MCP Validation]
    MCPValidate --> ValidateSuccess{Valid?}

    ValidateSuccess -->|Yes| FormatSuccess[Format SUCCESS Report]
    ValidateSuccess -->|No| MapErrors[Map Errors to Source]

    MapErrors --> ResolvePositions[Resolve Original Positions]
    ResolvePositions --> FormatErrors[Format ERROR Report]

    FormatSuccess --> Output([Output: Validation Report])
    FormatErrors --> Output
    ErrorCircular --> Output
    ErrorParse --> Output

    style Jinja2Path fill:#90EE90
    style LoadContext fill:#87CEEB
    style Render fill:#90EE90
    style BuildSourceMap1 fill:#FFD700
    style BuildSourceMap2 fill:#FFD700
    style LayerSourceMaps fill:#FFD700
    style MapErrors fill:#FFB6C1
    style ResolvePositions fill:#FFB6C1
```

---

## 3. Source Map Layers Architecture

```mermaid
graph LR
    subgraph "Original Source"
        O1[contract.j2.json L42]
        O2["type: {{ component_type }}"]
    end

    subgraph "Layer 1: Jinja2 Rendering"
        J1[Intermediate JSON L35]
        J2["type: StackView"]
        SM1[Jinja2 Source Map]
    end

    subgraph "Layer 2: Import Expansion"
        I1[Expanded JSON L38]
        I2["type: StackView + imported content"]
        SM2[Import Source Map]
    end

    subgraph "Layer 3: Final JSON"
        F1[Final JSON L156]
        F2["type: StackView"]
        SM3[Base Position Map]
    end

    subgraph "Error Resolution"
        E1[Error at L156]
        E2[Resolve via Source Maps]
        E3[Original L42]
    end

    O1 --> SM1
    SM1 --> J1
    J1 --> SM2
    SM2 --> I1
    I1 --> SM3
    SM3 --> F1

    F1 -.-> E1
    E1 --> E2
    E2 -.->|Reverse Lookup| SM3
    E2 -.->|Reverse Lookup| SM2
    E2 -.->|Reverse Lookup| SM1
    E2 --> E3

    style SM1 fill:#FFD700
    style SM2 fill:#FFD700
    style SM3 fill:#FFD700
    style E1 fill:#FF6B6B
    style E2 fill:#FFB6C1
    style E3 fill:#90EE90
```

---

## 4. Import Resolution & Dependency Graph

```mermaid
graph TD
    subgraph "Main Contract"
        Main[main_screen.j2.json]
    end

    subgraph "Imported Components"
        Coins[Coins.json]
        Header[Header.json]
        Footer[Footer.json]
        Logo[Logo.json]
        Links[Links.json]
        Copyright[Copyright.json]
    end

    subgraph "Import Processing"
        Parse[Parse Import Comments]
        Validate[Validate Paths]
        Graph[Build Dependency Graph]
        Detect[Detect Cycles]
        Resolve[Resolve in Bottom-Up Order]
        Cache[Cache Results]
    end

    Main -->|"// [Coins](file:///...)"| Coins
    Main -->|"// [Header](file:///...)"| Header
    Main -->|"// [Footer](file:///...)"| Footer

    Header -->|"// [Logo](file:///...)"| Logo
    Footer -->|"// [Links](file:///...)"| Links
    Footer -->|"// [Copyright](file:///...)"| Copyright

    Main --> Parse
    Parse --> Validate
    Validate --> Graph
    Graph --> Detect
    Detect -->|No Cycles| Resolve
    Resolve --> Cache

    Cache -.->|Invalidate on Change| Main
    Cache -.->|Invalidate on Change| Header
    Cache -.->|Invalidate on Change| Footer

    style Main fill:#87CEEB
    style Parse fill:#90EE90
    style Graph fill:#FFD700
    style Detect fill:#FFB6C1
    style Cache fill:#DDA0DD
```

**Resolution Order (Bottom-Up):**
1. Logo, Coins, Links, Copyright (no dependencies)
2. Header (depends on Logo), Footer (depends on Links, Copyright)
3. Main (depends on all)

**Invalidation Cascade (Top-Down):**
- Logo changes → invalidate Header → invalidate Main

---

## 5. Jinja2 Processing Architecture

```mermaid
sequenceDiagram
    participant V as Validator
    participant D as FormatDetector
    participant P as Jinja2Processor
    participant C as ContextProvider
    participant N as Nunjucks Engine
    participant S as SourceMapBuilder

    V->>D: Detect file format
    D->>D: Check extension (.j2.json)
    D->>D: Scan for Jinja2 syntax
    D-->>V: Format: Jinja2

    V->>P: Process Jinja2 template
    P->>C: Get rendering context

    alt Explicit context file exists
        C->>C: Load contract.context.json
        C-->>P: Return explicit context
    else Auto-generate context
        C->>C: Extract variables from template
        C->>C: Generate smart stubs
        C-->>P: Return auto-generated context
    end

    P->>N: Render template with context
    N->>N: Apply filters (now, formatCurrency, etc.)
    N->>N: Resolve {% include %} directives
    N-->>P: Rendered JSON string

    P->>S: Build source map
    S->>S: Track Jinja2 → JSON position mappings
    S-->>P: Jinja2SourceMap

    P-->>V: {rendered, sourceMap, dependencies}
```

---

## 6. Cache Architecture

```mermaid
graph TB
    subgraph "Cache Layer"
        Memory[In-Memory Cache Map]

        subgraph "Cached Entry"
            Meta[Metadata]
            Content[Content]
            Deps[Dependencies]
        end

        Invalidator[Cache Invalidator]
        DepGraph[Dependency Graph]
    end

    subgraph "Cache Operations"
        Get[Get Entry]
        Set[Set Entry]
        Invalidate[Invalidate Entry]
        Cascade[Cascade Invalidation]
    end

    subgraph "Triggers"
        FileChange[File Modified]
        DepChange[Dependency Changed]
        MemPressure[Memory Pressure]
    end

    Get --> Memory
    Set --> Memory
    Memory --> Meta
    Memory --> Content
    Memory --> Deps

    FileChange --> Invalidator
    DepChange --> Invalidator
    MemPressure --> Invalidator

    Invalidator --> Memory
    Invalidator --> DepGraph
    Invalidator --> Cascade

    Cascade -.->|Invalidate Dependents| Memory

    style Memory fill:#DDA0DD
    style Invalidator fill:#FFB6C1
    style DepGraph fill:#FFD700
    style Cascade fill:#FF6B6B
```

**Cache Entry Structure:**
```typescript
{
  filePath: "/path/to/file.j2.json",
  mtime: 1696512000000,
  contentHash: "abc123...",

  // Cached results
  jinja2Rendered: "...",
  importsResolved: Map<string, string>,
  positionMap: EnhancedPositionMap,
  validationReport: ValidationReport,

  // Dependency tracking
  dependencies: ["/path/to/dep1.json", "/path/to/dep2.json"],
  dependents: ["/path/to/parent.j2.json"]
}
```

---

## 7. Error Reporting Flow

```mermaid
flowchart TD
    Start[Validation Error Detected] --> Extract[Extract Error Details]
    Extract --> Path[Error Path: $.rootElement.type]
    Extract --> Msg[Error Message: Component not found]

    Path --> GetFinalPos[Get Final Position: L156]
    GetFinalPos --> ReverseLookup[Reverse Source Map Lookup]

    ReverseLookup --> CheckLayers{Check Source Map Layers}

    CheckLayers -->|Layer 3: Base| L3[Position in final JSON]
    CheckLayers -->|Layer 2: Import| L2[Position in expanded import]
    CheckLayers -->|Layer 1: Jinja2| L1[Position in Jinja2 template]
    CheckLayers -->|Layer 0: Original| L0[Position in .j2.json]

    L3 --> Confidence{Exact Match?}
    L2 --> Confidence
    L1 --> Confidence
    L0 --> Confidence

    Confidence -->|Exact| MarkExact[Confidence: exact]
    Confidence -->|Parent| MarkParent[Confidence: parent]
    Confidence -->|Fallback| MarkApprox[Confidence: approximate]

    MarkExact --> ExtractContext[Extract 3-line context]
    MarkParent --> ExtractContext
    MarkApprox --> ExtractContext

    ExtractContext --> BuildLink[Build clickable link]
    BuildLink --> FormatOutput[Format colored output]
    FormatOutput --> End([Display in VSCode])

    style Start fill:#FF6B6B
    style ReverseLookup fill:#FFD700
    style CheckLayers fill:#FFD700
    style ExtractContext fill:#87CEEB
    style BuildLink fill:#90EE90
    style End fill:#90EE90
```

**Error Report Example:**
```
❌ [1] Component StackViewXXX not found

    Path: $.rootElement.children[0].type
    JSON Pointer: /rootElement/children/0/type
    -> file:///path/to/contract.j2.json:42:5

    Context (contract.j2.json):
    41:     "children": [
    42:       "type": "{{ component_type }}",  ◄── Error here
    43:       "content": {

    Transformation Chain:
    • Original (.j2.json L42) → Jinja2 (L35) → Import (L38) → Final (L156)
    • Confidence: exact
```

---

## 8. Class Diagram (Core Components)

```mermaid
classDiagram
    class ValidationPipeline {
        +stages: ValidationStage[]
        +execute(filePath: string): ValidationReport
        -runStage(stage, context): StageContext
    }

    class ValidationStage {
        <<interface>>
        +process(context: StageContext): StageContext
    }

    class Jinja2ProcessingStage {
        -nunjucks: NunjucksEngine
        -contextProvider: ContextProvider
        +process(context): StageContext
        -renderTemplate(content, ctx): string
        -buildSourceMap(original, rendered): SourceMap
    }

    class ImportResolutionStage {
        -importParser: ImportParser
        -dependencyGraph: DependencyGraph
        +process(context): StageContext
        -parseImports(content): ImportDeclaration[]
        -resolveImports(imports): Map~string, string~
        -detectCircularDeps(graph): string[] | null
    }

    class PositionMappingStage {
        -sourceMapBuilder: SourceMapBuilder
        +process(context): StageContext
        -buildPositionMap(json): PositionMap
        -layerSourceMaps(maps[]): LayeredSourceMap
    }

    class LayeredSourceMap {
        -layers: SourceMapLayer[]
        +addLayer(layer): void
        +resolvePosition(line, col): ResolvedPosition
        +reverseResolve(file, line): Position
    }

    class CacheLayer {
        -memoryCache: Map~string, CachedEntry~
        -dependencyGraph: DependencyGraph
        +get(key): CachedEntry | null
        +set(key, entry): void
        +invalidate(key, reason): void
        -cascadeInvalidation(key): void
    }

    class ContextProvider {
        +loadContextFile(path): object | null
        +generateSmartContext(template): object
        +mergeContexts(contexts[]): object
    }

    ValidationPipeline --> ValidationStage
    ValidationStage <|-- Jinja2ProcessingStage
    ValidationStage <|-- ImportResolutionStage
    ValidationStage <|-- PositionMappingStage

    Jinja2ProcessingStage --> ContextProvider
    Jinja2ProcessingStage --> LayeredSourceMap
    ImportResolutionStage --> CacheLayer
    PositionMappingStage --> LayeredSourceMap
```

---

## 9. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        File[contract.j2.json]
        Context[contract.context.json]
    end

    subgraph "Stage 1: Load"
        Load[Read File Content]
        RawContent[Raw Content String]
    end

    subgraph "Stage 2: Detect"
        Detect[Format Detection]
        Format{.j2.json or Jinja2?}
    end

    subgraph "Stage 3: Jinja2"
        LoadCtx[Load Context]
        Render[Render Template]
        RenderedJSON[Rendered JSON String]
        SM1[Source Map 1]
    end

    subgraph "Stage 4: Imports"
        ParseImports[Parse Imports]
        ResolveImports[Resolve Dependencies]
        ExpandedJSON[Expanded JSON String]
        SM2[Source Map 2]
    end

    subgraph "Stage 5: Parse"
        ParseJSON[JSON.parse]
        ParsedData[Parsed JSON Object]
    end

    subgraph "Stage 6: Position"
        BuildPosMap[Build Position Map]
        LayerMaps[Layer Source Maps]
        FinalMap[Enhanced Position Map]
    end

    subgraph "Stage 7: Validate"
        MCPValidate[MCP Validator]
        RawReport[Raw Validation Report]
    end

    subgraph "Stage 8: Format"
        MapErrors[Map Errors to Source]
        FormatOutput[Format Output]
        FinalReport[Final Validation Report]
    end

    File --> Load
    Load --> RawContent
    RawContent --> Detect
    Detect --> Format

    Format -->|Yes| LoadCtx
    Context -.-> LoadCtx
    LoadCtx --> Render
    Render --> RenderedJSON
    Render --> SM1

    RenderedJSON --> ParseImports
    ParseImports --> ResolveImports
    ResolveImports --> ExpandedJSON
    ResolveImports --> SM2

    Format -->|No| ParseJSON
    ExpandedJSON --> ParseJSON
    ParseJSON --> ParsedData

    ParsedData --> BuildPosMap
    BuildPosMap --> LayerMaps
    SM1 -.-> LayerMaps
    SM2 -.-> LayerMaps
    LayerMaps --> FinalMap

    ParsedData --> MCPValidate
    MCPValidate --> RawReport

    RawReport --> MapErrors
    FinalMap -.-> MapErrors
    MapErrors --> FormatOutput
    FormatOutput --> FinalReport

    style RenderedJSON fill:#90EE90
    style ExpandedJSON fill:#90EE90
    style FinalMap fill:#FFD700
    style FinalReport fill:#87CEEB
```

---

## 10. Deployment Architecture

```mermaid
graph TB
    subgraph "Developer Machine"
        subgraph "VSCode"
            Editor[VSCode Editor]
            Extension[Run on Save Extension]
            Terminal[Integrated Terminal]
        end

        subgraph "File System"
            Scripts[/Users/username/Scripts/]
            Validator[vscode-validate-on-save_v2.3.0.js]
            Contracts[/Documents/FMS_GIT/_JSON/]
        end

        subgraph "Dependencies"
            NodeModules[node_modules/]
            Nunjucks[nunjucks]
            MCPSDK[alfa-sdui-mcp SDK]
        end
    end

    subgraph "External Services"
        MCP[alfa-sdui-mcp Server]
        SchemaRepo[Schema Repository]
    end

    Editor -->|Save| Extension
    Extension -->|Execute| Validator
    Validator --> Contracts
    Validator --> NodeModules
    NodeModules --> Nunjucks
    NodeModules --> MCPSDK
    MCPSDK -->|HTTP/IPC| MCP
    MCP --> SchemaRepo
    Validator -->|Results| Terminal
    Terminal -->|Display| Editor

    style Validator fill:#87CEEB
    style Nunjucks fill:#90EE90
    style MCP fill:#DDA0DD
```

**Installation:**
```bash
# Global installation
npm install -g vscode-validate-on-save@2.3.0

# Or local in Scripts/
cd /Users/username/Scripts
npm install vscode-validate-on-save@2.3.0
```

**VSCode Configuration:**
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [{
    "label": "Validate SDUI Contract",
    "type": "shell",
    "command": "node",
    "args": [
      "/Users/username/Scripts/vscode-validate-on-save_v2.3.0.js",
      "${file}"
    ],
    "problemMatcher": []
  }]
}

// .vscode/settings.json
{
  "emeraldwalk.runonsave": {
    "commands": [{
      "match": ".*\\.(json|j2\\.json)$",
      "cmd": "node /Users/username/Scripts/vscode-validate-on-save_v2.3.0.js ${file}"
    }]
  }
}
```

---

## 11. Performance Optimization Strategy

```mermaid
graph TD
    subgraph "Optimization Layers"
        L1[Layer 1: Fast Path Detection]
        L2[Layer 2: In-Memory Caching]
        L3[Layer 3: Incremental Processing]
        L4[Layer 4: Parallel Resolution]
    end

    subgraph "Fast Path (Pure JSON)"
        FP1[Skip Jinja2 Processing]
        FP2[Skip Import Resolution]
        FP3[Direct JSON.parse]
        FP4[Standard Position Map]
    end

    subgraph "Caching Strategy"
        C1[Template Compilation Cache]
        C2[Import Resolution Cache]
        C3[Position Map Cache]
        C4[Validation Report Cache]
    end

    subgraph "Incremental Processing"
        I1[Change Detection mtime/hash]
        I2[Dependency Graph Tracking]
        I3[Partial Invalidation]
        I4[Reuse Unchanged Results]
    end

    subgraph "Parallelization"
        P1[Parallel Import Resolution]
        P2[Async File I/O]
        P3[Worker Threads for Large Files]
    end

    L1 --> FP1
    FP1 --> FP2
    FP2 --> FP3
    FP3 --> FP4

    L2 --> C1
    L2 --> C2
    L2 --> C3
    L2 --> C4

    L3 --> I1
    I1 --> I2
    I2 --> I3
    I3 --> I4

    L4 --> P1
    L4 --> P2
    L4 --> P3

    style L1 fill:#90EE90
    style L2 fill:#DDA0DD
    style L3 fill:#FFD700
    style L4 fill:#87CEEB
```

**Performance Targets:**
- Pure JSON: < 200ms (no regression from v2.2.0)
- .j2.json < 50KB: < 500ms
- .j2.json < 200KB: < 1000ms
- Cache hit: < 50ms

---

## 12. Error Handling Strategy

```mermaid
stateDiagram-v2
    [*] --> FileLoad

    FileLoad --> FileNotFound: File not found
    FileLoad --> FormatDetect: Success

    FormatDetect --> Jinja2Process: .j2.json
    FormatDetect --> JSONParse: .json

    Jinja2Process --> RenderError: Syntax error
    Jinja2Process --> UndefinedVar: Undefined variable
    Jinja2Process --> ImportResolve: Success

    UndefinedVar --> ImportResolve: WARNING (continue)

    ImportResolve --> ImportNotFound: File not found
    ImportResolve --> CircularDep: Cycle detected
    ImportResolve --> JSONParse: Success

    ImportNotFound --> JSONParse: WARNING (skip import)

    JSONParse --> ParseError: Invalid JSON
    JSONParse --> PositionMap: Success

    PositionMap --> MCPValidate: Success

    MCPValidate --> ValidationError: Schema violation
    MCPValidate --> Success: Valid

    FileNotFound --> ErrorReport
    RenderError --> ErrorReport
    CircularDep --> ErrorReport
    ParseError --> ErrorReport
    ValidationError --> ErrorReport
    Success --> SuccessReport

    ErrorReport --> [*]
    SuccessReport --> [*]

    note right of UndefinedVar
        Graceful degradation:
        Use SafeDebugUndefined
    end note

    note right of ImportNotFound
        Partial validation:
        Continue without import
    end note

    note right of CircularDep
        Critical error:
        Abort with cycle path
    end note
```

**Error Severity Levels:**
- **CRITICAL:** Circular dependency, Jinja2 syntax error, JSON parse error
- **ERROR:** Missing required field, invalid component type
- **WARNING:** Undefined variable, missing import file, approximate position

---

## Conclusion

Эти диаграммы иллюстрируют ключевые аспекты архитектуры VSCode Validator v2.3.0:

1. **Modular Pipeline:** Изолированные stages для гибкости и тестируемости
2. **Layered Source Maps:** Точное отслеживание позиций через все трансформации
3. **Intelligent Caching:** Минимизация повторных вычислений
4. **Graceful Error Handling:** Partial validation при non-critical ошибках
5. **Performance Optimization:** Fast path для pure JSON, параллелизация, кеширование

Для детальных требований см. [полный PRD](./PRD_vscode_validator_v2.3.0.md).

---

**Prepared by:** Requirements Analysis Agent
**Date:** 2025-10-05
**Version:** 1.0
