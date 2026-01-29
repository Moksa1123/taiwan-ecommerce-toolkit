import cliProgress from 'cli-progress';
import chalk from 'chalk';

export interface InstallStep {
  name: string;
  weight: number;
}

export const INSTALL_STEPS: InstallStep[] = [
  { name: 'Checking for updates', weight: 10 },
  { name: 'Downloading release', weight: 25 },
  { name: 'Extracting files', weight: 15 },
  { name: 'Installing skill files', weight: 20 },
  { name: 'Installing references', weight: 10 },
  { name: 'Installing scripts', weight: 10 },
  { name: 'Installing data files', weight: 10 },
];

export const OFFLINE_STEPS: InstallStep[] = [
  { name: 'Loading templates', weight: 20 },
  { name: 'Generating skill files', weight: 30 },
  { name: 'Installing references', weight: 20 },
  { name: 'Installing scripts', weight: 15 },
  { name: 'Installing data files', weight: 15 },
];

export class InstallProgress {
  private bar: cliProgress.SingleBar;
  private currentStep: number = 0;
  private steps: InstallStep[];
  private totalWeight: number;
  private completedWeight: number = 0;

  constructor(steps: InstallStep[] = INSTALL_STEPS) {
    this.steps = steps;
    this.totalWeight = steps.reduce((sum, step) => sum + step.weight, 0);

    this.bar = new cliProgress.SingleBar({
      format: `${chalk.cyan('{bar}')} ${chalk.yellow('{percentage}%')} | ${chalk.dim('{step}')}`,
      barCompleteChar: '█',
      barIncompleteChar: '░',
      hideCursor: true,
      clearOnComplete: false,
      barsize: 30,
    });
  }

  start(): void {
    console.log();
    this.bar.start(100, 0, { step: this.steps[0]?.name || 'Starting...' });
  }

  nextStep(customName?: string): void {
    if (this.currentStep < this.steps.length) {
      this.completedWeight += this.steps[this.currentStep].weight;
      this.currentStep++;
    }

    const stepName = customName || this.steps[this.currentStep]?.name || 'Finishing...';
    const percentage = Math.min(Math.round((this.completedWeight / this.totalWeight) * 100), 99);

    this.bar.update(percentage, { step: stepName });
  }

  updateStep(name: string): void {
    this.bar.update(null, { step: name });
  }

  complete(): void {
    this.bar.update(100, { step: 'Complete!' });
    this.bar.stop();
    console.log();
  }

  fail(message: string): void {
    this.bar.stop();
    console.log();
    console.log(chalk.red(`✖ ${message}`));
  }
}

// Simpler animated progress for quick operations
export async function animatedDelay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
