"use client"

import { ColumnDef } from "@tanstack/react-table"

// This type is manually created for now.
// In a real app, you would generate this from your API schema.
export type Galaxy = {
  ra: number
  dec: number
  redshift: number
}

export const columns: ColumnDef<Galaxy>[] = [
  {
    accessorKey: "ra",
    header: "Right Ascension",
  },
  {
    accessorKey: "dec",
    header: "Declination",
  },
  {
    accessorKey: "redshift",
    header: "Redshift",
  },
]
