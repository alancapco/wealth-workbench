'use client';

import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from 'recharts';
import type { DateRange } from 'react-day-picker';
import { PageShell, PageHeader, SectionLabel } from '@/components/ui/WorkbenchUI';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Calendar } from '@/components/ui/calendar';
import { DatePicker } from '@/components/ui/date-picker';
import { DateRangePicker } from '@/components/ui/date-range-picker';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import { StatBlock, DataTableBlock, EmptyBlock } from '@/components/blocks';

// Component-preview values only — clearly labelled, never presented as client data.
const previewSeries = [
  { period: 'Q1', value: 18 },
  { period: 'Q2', value: 27 },
  { period: 'Q3', value: 22 },
  { period: 'Q4', value: 34 },
];
const chartConfig: ChartConfig = {
  value: { label: 'Sample value', color: 'hsl(var(--chart-1))' },
};

export default function UiKitPage() {
  const [date, setDate] = useState<Date | undefined>();
  const [range, setRange] = useState<DateRange | undefined>();
  const [notifications, setNotifications] = useState(true);
  const [consent, setConsent] = useState(false);
  const [segment, setSegment] = useState('hnw');

  return (
    <PageShell wide>
      <PageHeader
        eyebrow="Platform · Component library"
        title="shadcn/ui Kit"
        description="Buttons, form controls, calendar and date pickers, blocks and charts. Values shown here are component-preview samples, not client records."
      />

      <div className="space-y-5">
        <Alert>
          <AlertTitle>Component preview</AlertTitle>
          <AlertDescription>
            This page demonstrates the shared shadcn/ui primitives used across the workbench. All figures below are illustrative.
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Buttons &amp; badges</CardTitle>
              <CardDescription className="text-xs">Actions and status indicators</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-2">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Destructive</Button>
              <Button size="sm">Small</Button>
              <Separator orientation="vertical" className="mx-1 h-6" />
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="outline">Outline</Badge>
              <Badge variant="destructive">Attention</Badge>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Feedback &amp; overlays</CardTitle>
              <CardDescription className="text-xs">Tooltip, dialog, alert, skeleton</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="outline" size="sm">Hover me</Button>
                  </TooltipTrigger>
                  <TooltipContent>Contextual help for an RM</TooltipContent>
                </Tooltip>
              </TooltipProvider>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">Open dialog</Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Confirm an action</DialogTitle>
                    <DialogDescription>
                      shadcn Dialog provides focus trapping and keyboard dismissal.
                    </DialogDescription>
                  </DialogHeader>
                  <DialogFooter>
                    <DialogClose asChild><Button variant="ghost">Cancel</Button></DialogClose>
                    <DialogClose asChild><Button>Confirm</Button></DialogClose>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
              <Avatar><AvatarFallback>RM</AvatarFallback></Avatar>
              <Skeleton className="h-8 w-24" />
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Form controls</CardTitle>
            <CardDescription className="text-xs">Input, textarea, select, switch, checkbox, progress</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="kit-name">Client name</Label>
              <Input id="kit-name" placeholder="e.g. Tan Family Office" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kit-segment">Segment</Label>
              <Select value={segment} onValueChange={setSegment}>
                <SelectTrigger id="kit-segment"><SelectValue placeholder="Select segment" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hnw">HNW</SelectItem>
                  <SelectItem value="uhnw">UHNW</SelectItem>
                  <SelectItem value="family-office">Family office</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="kit-notes">Notes</Label>
              <Textarea id="kit-notes" rows={2} placeholder="Meeting notes" />
            </div>
            <div className="flex items-center gap-2">
              <Switch id="kit-notify" checked={notifications} onCheckedChange={setNotifications} />
              <Label htmlFor="kit-notify">Notifications {notifications ? 'on' : 'off'}</Label>
            </div>
            <div className="flex items-center gap-2">
              <Checkbox id="kit-consent" checked={consent} onCheckedChange={(v) => setConsent(v === true)} />
              <Label htmlFor="kit-consent">Consent recorded</Label>
            </div>
            <div className="space-y-2">
              <Label className="text-xs text-muted-foreground">Review progress</Label>
              <Progress value={64} />
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Calendar &amp; date pickers</CardTitle>
              <CardDescription className="text-xs">Single date, range and inline calendar</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label className="text-xs">From date</Label>
                  <DatePicker value={date} onChange={setDate} />
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Date range</Label>
                  <DateRangePicker value={range} onChange={setRange} />
                </div>
              </div>
              <Calendar mode="single" selected={date} onSelect={setDate} className="rounded-md border" />
            </CardContent>
            <CardFooter className="text-xs text-muted-foreground">
              Calendar is also wired into the live Calendar &amp; Meetings workspace as a period filter.
            </CardFooter>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Chart</CardTitle>
              <CardDescription className="text-xs">recharts through shadcn ChartContainer</CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer config={chartConfig} className="h-[260px] w-full">
                <BarChart data={previewSeries} margin={{ left: 0, right: 12, top: 8 }}>
                  <CartesianGrid vertical={false} stroke="hsl(var(--border))" />
                  <XAxis dataKey="period" tickLine={false} axisLine={false} tickMargin={8} fontSize={11} />
                  <YAxis tickLine={false} axisLine={false} tickMargin={8} fontSize={11} width={36} />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Bar dataKey="value" fill="var(--color-value)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </div>

        <SectionLabel>Blocks</SectionLabel>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <StatBlock label="Sample AUM" value="SGD 120.5M" sub="Preview value" />
          <StatBlock label="Sample entities" value="7" sub="Preview value" />
          <StatBlock label="Sample coverage" value="92%" trend={<Badge variant="outline">Preview</Badge>} />
        </div>

        <Tabs defaultValue="table">
          <TabsList>
            <TabsTrigger value="table">Table block</TabsTrigger>
            <TabsTrigger value="empty">Empty block</TabsTrigger>
          </TabsList>
          <TabsContent value="table" className="mt-3">
            <DataTableBlock
              title="Sample holdings"
              subtitle="Composed Card + Table block (preview rows)"
              columns={[
                { key: 'name', label: 'Instrument' },
                { key: 'weight', label: 'Weight', align: 'right' },
              ]}
              rows={[
                { name: 'Global equity', weight: '48%' },
                { name: 'Fixed income', weight: '35%' },
                { name: 'Cash', weight: '17%' },
              ]}
            />
          </TabsContent>
          <TabsContent value="empty" className="mt-3">
            <Card><CardContent className="p-0"><EmptyBlock title="Nothing to show" detail="Empty blocks follow the same shadcn card styling." /></CardContent></Card>
          </TabsContent>
        </Tabs>
      </div>
    </PageShell>
  );
}
