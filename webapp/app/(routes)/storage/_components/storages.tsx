import createApiClient from "packages/sdk/api";
import { UserStorage } from "packages/sdk";
import { DataTable } from "@/components/data-table";
import { columns } from "./columns";

const api = createApiClient({
  baseUrl: "http://localhost:8000",
});

async function getStorages(): Promise<UserStorage[]> {
  const { data, error } = await api.GET("/storage/list", {
    next: { revalidate: 0 },
  });

  if (error) {
    throw new Error("Failed to fetch storages");
  }

  return data.storages;
}

export async function Storages() {
  let data: UserStorage[] = [];
  let error: string | null = null;

  try {
    data = await getStorages();
  } catch (e: any) {
    error = e.message;
  }

  return (
    <div>
      <h3 className="text-lg font-medium">Existing Storage</h3>
      <p className="text-sm text-muted-foreground">
        View and manage your existing storage buckets.
      </p>
      <div className="mt-4">
        {error ? (
          <p className="text-sm text-red-500">{error}</p>
        ) : (
          <DataTable columns={columns} data={data} />
        )}
      </div>
    </div>
  );
}
