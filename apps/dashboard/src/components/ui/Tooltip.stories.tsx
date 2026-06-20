import type { Meta, StoryObj } from "@storybook/nextjs";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "./Tooltip";
import { Button } from "./Button";

const meta: Meta<typeof Tooltip> = {
  title: "UI/Tooltip",
  component: Tooltip,
  tags: ["autodocs"],
};

export default meta;
/** Module-internal — do not consume from outside. */
type Story = StoryObj<typeof Tooltip>;

export const Default: Story = {
  render: () => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Hover me</Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>This is a tooltip</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};

export const WithDescription: Story = {
  render: () => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button>Settings</Button>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-semibold">Configure settings</p>
          <p className="text-xs text-muted-foreground">Manage your account preferences</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ),
};
