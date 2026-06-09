import * as vscode from 'vscode';

export class MutantTreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly status: string,
    public readonly mutantId?: string,
    public readonly collapsibleState?: vscode.TreeItemCollapsibleState,
    public readonly command?: vscode.Command,
    public readonly typeKey?: string, // Category routing identifier
    public readonly accepted?: boolean
  ) {
    super(label, collapsibleState ?? vscode.TreeItemCollapsibleState.None);
    if (typeKey) {
      if (typeKey.startsWith('file_child:')) {
        this.contextValue = 'file_parent_category';
      } else {
        this.contextValue = typeKey;
      }
    } else {
      this.contextValue = 'mutantItem';
    }
    
    if (accepted !== undefined) {
      this.description = accepted ? '✅ ACCEPTED' : '❌ REJECTED';
    }

    this.tooltip = `${this.label} (${this.status})`;
    
    // Customize section-specific icons
    if (status === 'KILLED' || status === 'PASSED') {
      this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
    } else if (status === 'SURVIVED' || status === 'FAILED') {
      this.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'));
    } else if (status === 'PENDING' || status === 'RUNNING') {
      this.iconPath = new vscode.ThemeIcon('play', new vscode.ThemeColor('testing.iconQueued'));
    } else if (status === 'SECTION_HEADER') {
      this.iconPath = new vscode.ThemeIcon('symbol-class');
    } else if (status === 'SUB_HEADER') {
      this.iconPath = new vscode.ThemeIcon('file-code');
    } else {
      this.iconPath = new vscode.ThemeIcon('circle-outline');
    }
  }
}

export class MutationTreeDataProvider implements vscode.TreeDataProvider<MutantTreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<MutantTreeItem | undefined | null | void> = 
    new vscode.EventEmitter<MutantTreeItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<MutantTreeItem | undefined | null | void> = 
    this._onDidChangeTreeData.event;

  // Track dynamic sections status
  private baselineTests: any[] = [];
  private mutants: any[] = [];
  private executionRuns: any[] = [];

  constructor() {}

  refresh(data: { baseline?: any[]; mutants?: any[]; runs?: any[] }): void {
    if (data.baseline !== undefined) { this.baselineTests = data.baseline; }
    if (data.mutants !== undefined) { this.mutants = data.mutants; }
    if (data.runs !== undefined) { this.executionRuns = data.runs; }
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: MutantTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: MutantTreeItem): Thenable<MutantTreeItem[]> {
    if (!element) {
      // ══════════════════════════════════════════════════════════════
      // Root Node Categorized Sections
      // ══════════════════════════════════════════════════════════════
      const sections: MutantTreeItem[] = [];

      // Section 1: Baseline Tests
      const baselineStatus = this.baselineTests.length > 0 
        ? `${this.baselineTests.filter(t => t.status === 'PASSED').length}/${this.baselineTests.length} PASSED`
        : 'Not Executed';
      sections.push(new MutantTreeItem(
        `🧪 Baseline Tests: [${baselineStatus}]`,
        'SECTION_HEADER',
        undefined,
        vscode.TreeItemCollapsibleState.Expanded,
        undefined,
        'baseline_category'
      ));

      // Section 2: Scan & Generate Mutants
      const mutantStatus = this.mutants.length > 0
        ? `${this.mutants.length} Nominees`
        : 'No Nominees';
      sections.push(new MutantTreeItem(
        `🔍 Generated Mutants: [${mutantStatus}]`,
        'SECTION_HEADER',
        undefined,
        vscode.TreeItemCollapsibleState.Expanded,
        undefined,
        'scan_category'
      ));

      // Section 3: Execute Mutation Run
      const killed = this.executionRuns.filter(r => r.status === 'KILLED').length;
      const survived = this.executionRuns.filter(r => r.status === 'SURVIVED').length;
      const score = this.executionRuns.length > 0 ? ((killed / this.executionRuns.length) * 100).toFixed(1) : '0.0';
      const runStatus = this.executionRuns.length > 0
        ? `Kill Score: ${score}% (${killed} Killed, ${survived} Survived)`
        : 'No Runs Evaluated';
      sections.push(new MutantTreeItem(
        `🧬 Mutation Testing Runs: [${runStatus}]`,
        'SECTION_HEADER',
        undefined,
        vscode.TreeItemCollapsibleState.Expanded,
        undefined,
        'run_category'
      ));

      return Promise.resolve(sections);
    }

    // ══════════════════════════════════════════════════════════════
    // Child Categories Expansion Routing
    // ══════════════════════════════════════════════════════════════
    const categoryType = element.typeKey;

    if (categoryType === 'baseline_category') {
      if (this.baselineTests.length === 0) {
        return Promise.resolve([new MutantTreeItem('No baseline tests executed yet.', 'INFO')]);
      }
      return Promise.resolve(this.baselineTests.map(t => {
        return new MutantTreeItem(
          `${t.name} (${t.durationMs}ms)`,
          t.status,
          undefined,
          vscode.TreeItemCollapsibleState.None
        );
      }));
    }

    if (categoryType === 'scan_category') {
      if (this.mutants.length === 0) {
        return Promise.resolve([new MutantTreeItem('No mutants scanned yet. Click "Scan Mutants" to begin.', 'INFO')]);
      }
      
      // Group logically by File Path
      const fileGroups: { [key: string]: any[] } = {};
      this.mutants.forEach(m => {
        let file = m.file_path || 'agent/hello.py';
        file = normalizeLanguagePath(file);
        if (!fileGroups[file]) { fileGroups[file] = []; }
        fileGroups[file].push(m);
      });

      const fileItems = Object.keys(fileGroups).map(file => {
        return new MutantTreeItem(
          file,
          'SUB_HEADER',
          undefined,
          vscode.TreeItemCollapsibleState.Expanded,
          undefined,
          `file_child:${file}`
        );
      });
      return Promise.resolve(fileItems);
    }

    if (categoryType && categoryType.startsWith('file_child:')) {
      const fileTarget = categoryType.substring(11);
      const fileMutants = this.mutants.filter(m => {
        let file = m.file_path || 'agent/hello.py';
        file = normalizeLanguagePath(file);
        return file === fileTarget;
      });

      return Promise.resolve(fileMutants.map(m => {
        const opMap: { [key: string]: string } = {
          'sub': '-', 'add': '+', 'mul': '*', 'div': '/', 'FloorDiv': '//', 'Mod': '%',
          'GtE': '>=', 'Gt': '>', 'LtE': '<=', 'Lt': '<',
          'Eq': '==', 'NotEq': '!=', 'And': 'and', 'Or': 'or',
          'mult': '*'
        };
        const prettyMut = opMap[m.mutated_value] || m.mutated_value;
        const origCode = opMap[m.original_code] || m.original_code;
        const label = `Line ${m.line_number}: replace '${origCode}' with '${prettyMut}' [${m.operator_type}]`;
        const cmd: vscode.Command = {
          title: 'Show Diff',
          command: 'mutation.showDiff',
          arguments: [m]
        };
        return new MutantTreeItem(
          label,
          m.status || 'PENDING',
          m.mutant_id,
          vscode.TreeItemCollapsibleState.None,
          cmd,
          undefined,
          m.accepted
        );
      }));
    }

    if (categoryType === 'run_category') {
      if (this.executionRuns.length === 0) {
        return Promise.resolve([new MutantTreeItem('No sandbox runs executed yet.', 'INFO')]);
      }
      return Promise.resolve(this.executionRuns.map(r => {
        // Find line number from original cached mutant if not directly provided on run result
        let lineNo = r.line_number;
        if (!lineNo) {
          const matchedMutant = this.mutants.find(m => m.mutant_id === r.mutantId);
          if (matchedMutant) {
            lineNo = matchedMutant.line_number;
          }
        }
        const label = `Line ${lineNo || '?'}: ${r.mutantId} -> Status: ${r.status}`;
        const cmd: vscode.Command = {
          title: 'Show Diff',
          command: 'mutation.showDiff',
          arguments: [r]
        };
        return new MutantTreeItem(
          label,
          r.status,
          r.mutantId,
          vscode.TreeItemCollapsibleState.None,
          cmd
        );
      }));
    }

    return Promise.resolve([]);
  }
}

function normalizeLanguagePath(filePath: string): string {
  const lower = filePath.toLowerCase();
  if (lower.includes('hello.cpp') || lower.endsWith('hello.cpp')) {
    return 'agent/hello.cpp';
  }
  if (lower.includes('hello.py') || lower.endsWith('hello.py')) {
    return 'agent/hello.py';
  }
  // Fallback to relative string path clean-up
  return filePath.replace(/\\/g, '/');
}
