import createApiClient from "packages/sdk/api";
import { columns } from "./columns";
import { DataTable } from "@/components/data-table";
import { Galaxy } from "./columns";

const api = createApiClient({
  baseUrl: "http://localhost:8000",
});

async function getData(): Promise<Galaxy[]> {
  const { data, error } = await api.GET("/science/data", {
    next: { revalidate: 60 },
  });

  if (error) {
    // In a real application, you'd want to handle this error more gracefully
    console.error(error);
    return [];
  }

  return data.data;
}

export default async function TaskPage() {
  const data = await getData();

  return (
    <>
      <div className="h-full flex-1 flex-col space-y-8 p-8 flex">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Galaxy Survey Data</h2>
            <p className="text-muted-foreground">
              A read-only view of galaxy survey data fetched from the backend.
            </p>
          </div>
        </div>
        <DataTable data={data} columns={columns} />
      </div>
    </>
  );
}
