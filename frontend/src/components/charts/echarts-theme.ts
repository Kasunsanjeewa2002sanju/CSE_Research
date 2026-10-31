import { echarts } from './echarts-setup';

/**
 * Institutional Research ECharts Theme
 * Generated strictly from the 60/30/10 tokens and semantic market palettes.
 */
export const CSE_RESEARCH_THEME_NAME = 'cse-research';

export const themeTokens = {
  navy: '#0A2A66',
  blueNavy: '#0A2A66',
  blueCobalt: '#1246B3',
  blueVibrant: '#1B5CD6',
  blueIce: '#EEF4FF',
  accent: '#00B8D9',
  accentHover: '#0095B3',
  dataUp: '#0F9D6B',
  dataDown: '#D93A3A',
  dataWarning: '#E39B0B',
  text: '#0B1B33',
  muted: '#53627A',
  border: '#E1E8F2',
};

export const cseResearchEChartsTheme = {
  color: [
    '#1B5CD6', // Primary Series Blue
    '#00B8D9', // Cyan Accent
    '#0A2A66', // Deep Navy
    '#0F9D6B', // Up / Positive Return
    '#D93A3A', // Down / Negative Return
    '#E39B0B', // Warning / Event Shock
    '#1246B3', // Cobalt
    '#7987A0', // Neutral Series
  ],
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    color: '#0B1B33',
    fontSize: 12,
  },
  title: {
    textStyle: {
      fontFamily: 'Manrope, sans-serif',
      fontWeight: 700,
      color: '#0A2A66',
      fontSize: 14,
    },
    subtextStyle: {
      color: '#53627A',
      fontSize: 11,
    },
  },
  line: {
    itemStyle: {
      borderWidth: 2,
    },
    lineStyle: {
      width: 2.5,
    },
    symbol: 'circle',
    symbolSize: 4,
    smooth: true,
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '8%',
    top: '12%',
    containLabel: true,
    borderColor: '#E1E8F2',
  },
  categoryAxis: {
    axisLine: {
      show: true,
      lineStyle: {
        color: '#CAD5E2',
      },
    },
    axisTick: {
      show: false,
    },
    axisLabel: {
      color: '#53627A',
      fontSize: 11,
      fontFamily: '"JetBrains Mono", monospace',
    },
    splitLine: {
      show: false,
    },
  },
  valueAxis: {
    axisLine: {
      show: false,
    },
    axisTick: {
      show: false,
    },
    axisLabel: {
      color: '#53627A',
      fontSize: 11,
      fontFamily: '"JetBrains Mono", monospace',
    },
    splitLine: {
      show: true,
      lineStyle: {
        color: '#E1E8F2',
        type: 'dashed',
      },
    },
  },
  tooltip: {
    backgroundColor: '#FFFFFF',
    borderColor: '#CAD5E2',
    borderWidth: 1,
    padding: [8, 12],
    textStyle: {
      color: '#0B1B33',
      fontSize: 12,
      fontFamily: '"JetBrains Mono", monospace',
    },
    extraCssText: 'box-shadow: 0 4px 16px rgba(11, 27, 51, 0.08); border-radius: 8px;',
    axisPointer: {
      type: 'cross',
      lineStyle: {
        color: '#1B5CD6',
        width: 1,
        type: 'dashed',
      },
      crossStyle: {
        color: '#1B5CD6',
      },
    },
  },
  dataZoom: {
    borderColor: '#E1E8F2',
    textStyle: {
      color: '#53627A',
      fontFamily: '"JetBrains Mono", monospace',
      fontSize: 10,
    },
    fillerColor: 'rgba(201, 219, 250, 0.35)',
    handleIcon:
      'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
    handleSize: '80%',
    handleStyle: {
      color: '#1B5CD6',
      shadowBlur: 3,
      shadowColor: 'rgba(0, 0, 0, 0.2)',
    },
    dataBackground: {
      lineStyle: {
        color: '#1B5CD6',
        width: 1,
      },
      areaStyle: {
        color: '#C9DBFA',
      },
    },
  },
  visualMap: {
    color: ['#0F9D6B', '#EEF3FA', '#D93A3A'], // Diverging: green -> neutral -> red
    textStyle: {
      color: '#53627A',
      fontFamily: 'Inter, sans-serif',
      fontSize: 11,
    },
  },
};

// Register theme with ECharts singleton
echarts.registerTheme(CSE_RESEARCH_THEME_NAME, cseResearchEChartsTheme);
