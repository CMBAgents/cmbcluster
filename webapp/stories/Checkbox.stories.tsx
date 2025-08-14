import type { Meta, StoryObj } from '@storybook/react';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';

const meta: Meta<typeof Checkbox> = {
  title: 'ui/Checkbox',
  component: Checkbox,
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Checkbox>;

export const Default: Story = {
  render: (args) => (
    <div className="flex items-center space-x-2">
      <Checkbox id="terms" {...args} />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
  ),
};

export const Disabled: Story = {
    render: (args) => (
      <div className="flex items-center space-x-2">
        <Checkbox id="terms" {...args} />
        <Label htmlFor="terms">Accept terms and conditions</Label>
      </div>
    ),
    args: {
        disabled: true,
    }
  };
