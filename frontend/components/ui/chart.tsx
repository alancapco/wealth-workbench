"use client"

import * as React from "react"
import * as RechartsPrimitive from "recharts"

import { cn } from "@/lib/utils"

/**
 * Canonical shadcn/ui chart surface, kept compatible with recharts 3 /
 * React 18 / Next 14 / Tailwind 3.4. It exposes the same public API as the
 * registry component: ChartContainer, ChartTooltip, ChartTooltipContent,
 * ChartLegend, ChartLegendContent and the ChartConfig type.
 */
export type ChartConfig = {
  [key: string]: {
    label?: React.ReactNode
    icon?: React.ComponentType<{ className?: string }>
    color?: string
    theme?: Record<string, string>
  }
}

type ChartContextProps = { config: ChartConfig }

const ChartContext = React.createContext<ChartContextProps | null>(null)

function useChart() {
  const context = React.useContext(ChartContext)
  if (!context) {
    throw new Error("useChart must be used within a <ChartContainer />")
  }
  return context
}

const ChartContainer = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & {
    config: ChartConfig
    children: React.ReactNode
  }
>(({ id, className, children, config, ...props }, ref) => {
  const uniqueId = React.useId()
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-chart={chartId}
        ref={ref}
        className={cn(
          "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-dot[stroke='#fff']]:stroke-transparent [&_.recharts-layer]:outline-none [&_.recharts-polar-grid_[stroke='#ccc']]:stroke-border [&_.recharts-radial-bar-background-sector]:fill-muted [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_[stroke='#ccc']]:stroke-border [&_.recharts-sector]:outline-none [&_.recharts-surface]:outline-none",
          className
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  )
})
ChartContainer.displayName = "ChartContainer"

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
  const entries = Object.entries(config).filter(([, c]) => c.color || c.theme)
  if (!entries.length) return null

  const block = (selector: string, themeName: string) =>
    `${selector} [data-chart=${id}] {\n${entries
      .map(([key, c]) => {
        const color = (c.theme && c.theme[themeName]) || c.color
        return color ? `  --color-${key}: ${color};` : null
      })
      .filter(Boolean)
      .join("\n")}\n}`

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: `${block(":root", "light")}\n${block(".dark", "dark")}`,
      }}
    />
  )
}

const ChartTooltip = RechartsPrimitive.Tooltip

type PayloadItem = {
  name?: string | number
  value?: any
  dataKey?: string | number
  color?: string
  fill?: string
  payload?: Record<string, any>
  [key: string]: any
}

function getPayloadConfig(
  config: ChartConfig,
  item: PayloadItem,
  key: string
): ChartConfig[string] | undefined {
  const nested = item.payload?.[key] ?? item[key]
  const configKey = typeof nested === "string" ? nested : key
  return config[configKey] || config[key]
}

const ChartTooltipContent = ({
  active,
  payload,
  label,
  labelFormatter,
  formatter,
  hideLabel = false,
  hideIndicator = false,
  nameKey,
  indicator = "dot",
  labelClassName,
  className,
}: {
  active?: boolean
  payload?: PayloadItem[]
  label?: React.ReactNode
  labelFormatter?: (
    label: React.ReactNode,
    payload: PayloadItem[]
  ) => React.ReactNode
  formatter?: (
    value: any,
    name: any,
    item: PayloadItem,
    index: number,
    payload: any
  ) => React.ReactNode
  hideLabel?: boolean
  hideIndicator?: boolean
  nameKey?: string
  labelKey?: string
  indicator?: "line" | "dot" | "dashed"
  labelClassName?: string
  className?: string
}) => {
  const { config } = useChart()

  if (!active || !payload || !payload.length) return null

  const shownLabel = !hideLabel ? (
    <div className={cn("font-medium", labelClassName)}>
      {labelFormatter ? labelFormatter(label, payload) : label}
    </div>
  ) : null

  return (
    <div
      className={cn(
        "grid min-w-[8rem] items-start gap-1.5 rounded-lg border border-border/50 bg-background px-2.5 py-1.5 text-xs shadow-xl",
        className
      )}
    >
      {shownLabel}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || "value"}`
          const itemConfig = getPayloadConfig(config, item, key)
          const indicatorColor = item.color || item.fill || item.payload?.fill

          return (
            <div
              key={`${item.dataKey ?? index}`}
              className={cn(
                "flex w-full flex-wrap items-stretch gap-2",
                indicator === "dot" && "items-center"
              )}
            >
              {formatter && item.value !== undefined && item.name ? (
                formatter(item.value, item.name, item, index, item.payload)
              ) : (
                <>
                  {!hideIndicator && (
                    <div
                      className={cn("shrink-0 rounded-[2px]", {
                        "h-2.5 w-2.5": indicator === "dot",
                        "w-1": indicator === "line",
                        "w-0 border-[1.5px] border-dashed bg-transparent":
                          indicator === "dashed",
                      })}
                      style={{
                        backgroundColor: indicatorColor,
                        borderColor: indicatorColor,
                      }}
                    />
                  )}
                  <div className="flex flex-1 items-center justify-between gap-2 leading-none">
                    <span className="text-muted-foreground">
                      {itemConfig?.label || item.name}
                    </span>
                    {item.value !== undefined && (
                      <span className="font-mono font-medium tabular-nums text-foreground">
                        {typeof item.value === "number"
                          ? item.value.toLocaleString("en-US")
                          : item.value}
                      </span>
                    )}
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

const ChartLegend = RechartsPrimitive.Legend

const ChartLegendContent = ({
  className,
  hideIcon = false,
  payload,
  nameKey,
}: {
  className?: string
  hideIcon?: boolean
  payload?: Array<{
    value?: string | number
    color?: string
    dataKey?: string | number
  }>
  nameKey?: string
  verticalAlign?: "top" | "bottom"
}) => {
  const { config } = useChart()

  if (!payload?.length) return null

  return (
    <div className={cn("flex items-center justify-center gap-4", className)}>
      {payload.map((item, index) => {
        const key = `${nameKey || item.dataKey || item.value || "value"}`
        const itemConfig = config[key]
        return (
          <div
            key={`${item.value ?? index}`}
            className="flex items-center gap-1.5"
          >
            {!hideIcon && (
              <div
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{ backgroundColor: item.color }}
              />
            )}
            <span className="text-muted-foreground">
              {itemConfig?.label || item.value}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  ChartStyle,
  useChart,
}
