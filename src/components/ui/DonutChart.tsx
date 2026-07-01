import React from 'react';
import { View } from 'react-native';
import Svg, { Circle, G } from 'react-native-svg';

export interface DonutDataPoint {
  label: string;
  count: number;
  color: string;
}

export function DonutChart({ data, size = 120, strokeWidth = 16 }: { data: DonutDataPoint[], size?: number, strokeWidth?: number }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const total = data.reduce((sum, item) => sum + item.count, 0);

  let currentOffset = 0;

  return (
    <View style={{ alignItems: 'center', justifyContent: 'center', width: size, height: size }}>
      <Svg width={size} height={size}>
        <G rotation="-90" origin={`${size / 2}, ${size / 2}`}>
          {total === 0 ? (
            <Circle
              stroke="#E5E7EB"
              fill="none"
              cx={size / 2}
              cy={size / 2}
              r={radius}
              strokeWidth={strokeWidth}
            />
          ) : (
            data.map((item, index) => {
              const strokeLength = (item.count / total) * circumference;
              const offset = currentOffset;
              currentOffset += strokeLength;

              if (item.count === 0) return null;

              return (
                <Circle
                  key={index}
                  stroke={item.color}
                  fill="none"
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  strokeWidth={strokeWidth}
                  strokeDasharray={`${strokeLength} ${circumference}`}
                  strokeDashoffset={-offset}
                />
              );
            })
          )}
        </G>
      </Svg>
    </View>
  );
}
