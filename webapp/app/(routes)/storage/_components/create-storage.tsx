"use client";

import { useFormState } from "react-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SubmitButton } from "./submit-button";
import { createStorage } from "../actions";

const initialState = {
  message: "",
};

export function CreateStorage() {
  const [state, formAction] = useFormState(createStorage, initialState);

  return (
    <div>
      <h3 className="text-lg font-medium">Create New Storage</h3>
      <p className="text-sm text-muted-foreground">
        Create a new storage bucket to store your data.
      </p>
      <form action={formAction} className="mt-4 space-y-4">
        <div className="grid w-full max-w-sm items-center gap-1.5">
          <Label htmlFor="custom_name">Custom Name</Label>
          <Input
            type="text"
            id="custom_name"
            name="custom_name"
            placeholder="my-storage-bucket"
            required
          />
        </div>
        <div className="grid w-full max-w-sm items-center gap-1.5">
          <Label htmlFor="storage_class">Storage Class</Label>
          <Select name="storage_class" required>
            <SelectTrigger>
              <SelectValue placeholder="Select a storage class" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="STANDARD">Standard</SelectItem>
              <SelectItem value="NEARLINE">Nearline</SelectItem>
              <SelectItem value="COLDLINE">Coldline</SelectItem>
              <SelectItem value="ARCHIVE">Archive</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="grid w-full max-w-sm items-center gap-1.5">
          <Label htmlFor="location">Location</Label>
          <Input
            type="text"
            id="location"
            name="location"
            placeholder="us-central1"
            required
          />
        </div>
        <SubmitButton>Create Storage</SubmitButton>
        {state?.message && (
          <p className="text-sm text-red-500">{state.message}</p>
        )}
      </form>
    </div>
  );
}
