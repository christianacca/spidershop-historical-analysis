export interface SparklineBarData {
  bar_height: number;
  fill: string;
  opacity: number;
  tooltip: string;
}

export interface SparklineDto {
  bars: (SparklineBarData | null)[];
  svg_width: number;
  svg_height: number;
  title: string;
}
