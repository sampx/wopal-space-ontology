import type { LoggerInstance } from "../logger.js"
import { coreLogger } from "../logger.js"

export interface MonitorStrategy {
  name: string
  tick(): Promise<void>
}

export class MonitorEngine {
  private readonly strategies: MonitorStrategy[]
  private readonly intervalMs: number
  private readonly logger: LoggerInstance
  private timer: ReturnType<typeof setInterval> | undefined = undefined
  private tickRunning = false
  private stopped = false

  constructor(args: {
    intervalMs?: number
    strategies: MonitorStrategy[]
    logger?: LoggerInstance
  }) {
    this.intervalMs = args.intervalMs ?? 30_000
    this.strategies = args.strategies
    this.logger = args.logger ?? coreLogger
  }

  start(): void {
    if (this.timer) return
    if (this.stopped) return

    this.timer = setInterval(() => {
      if (this.tickRunning) return
      this.tickRunning = true
      void this.runTick().finally(() => {
        this.tickRunning = false
      })
    }, this.intervalMs)
    this.timer.unref()
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer)
    }
    this.timer = undefined
    this.stopped = true
  }

  shutdown(): void {
    this.stop()
  }

  async runOnceForTesting(): Promise<void> {
    await this.runTick()
  }

  private async runTick(): Promise<void> {
    for (const strategy of this.strategies) {
      try {
        await strategy.tick()
      } catch (error) {
        this.logger.error(
          { err: error instanceof Error ? error : new Error(String(error)), strategy: strategy.name },
          `[monitor] strategy ${strategy.name} failed`,
        )
      }
    }
  }
}
