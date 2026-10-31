import * as echarts from 'echarts/core';
import {
  LineChart,
  BarChart,
  ScatterChart,
  HeatmapChart,
  EffectScatterChart,
  BoxplotChart,
  LinesChart,
  CustomChart,
  PieChart,
} from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  DataZoomInsideComponent,
  DataZoomSliderComponent,
  MarkLineComponent,
  MarkAreaComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  TransformComponent,
  BrushComponent,
  VisualMapComponent,
  ToolboxComponent,
  GraphicComponent,
  AriaComponent,
  CalendarComponent,
} from 'echarts/components';
import { UniversalTransition, LabelLayout, LegacyGridContainLabel } from 'echarts/features';
import { CanvasRenderer } from 'echarts/renderers';

// Register all required charts, components, and renderers with ECharts
echarts.use([
  // Features
  UniversalTransition,
  LabelLayout,
  LegacyGridContainLabel,

  // Charts
  LineChart,
  BarChart,
  ScatterChart,
  HeatmapChart,
  EffectScatterChart,
  BoxplotChart,
  LinesChart,
  CustomChart,
  PieChart,

  // Components
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  DataZoomInsideComponent,
  DataZoomSliderComponent,
  MarkLineComponent,
  MarkAreaComponent,
  LegendComponent,
  TitleComponent,
  DatasetComponent,
  TransformComponent,
  BrushComponent,
  VisualMapComponent,
  ToolboxComponent,
  GraphicComponent,
  AriaComponent,
  CalendarComponent,

  // Renderer
  CanvasRenderer,
]);

export { echarts };
export type { ECharts, EChartsOption } from 'echarts';
