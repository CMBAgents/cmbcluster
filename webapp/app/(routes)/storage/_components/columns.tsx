"use client";

import { UserStorage } from "packages/sdk";
import { ColumnDef } from "@tanstack/react-table";

export const columns: ColumnDef<UserStorage>[] = [
  {
    accessorKey: "display_name",
    header: "Display Name",
  },
  {
    accessorKey: "bucket_name",
    header: "Bucket Name",
  },
  {
    accessorKey: "status",
    header: "Status",
  },
  {
    accessorKey: "location",
    header: "Location",
  },
  {
    accessorKey: "storage_class",
    header: "Storage Class",
  },
];
