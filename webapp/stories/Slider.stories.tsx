import type { Meta, StoryObj } from '@storybook/react';
import { Slider } from '../components/ui/slider';

const meta: Meta<typeof Slider> = {
  title: 'ui/Slider',
  component: Slider,
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Slider>;

export const Default: Story = {
  args: {
    defaultValue: [50],
    max: 100,
    step: 1,
  },
};

export const Disabled: Story = {
    args: {
      defaultValue: [50],
      max: 100,
      step: 1,
      disabled: true,
    },
  };
