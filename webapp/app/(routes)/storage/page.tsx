import { Storages } from "./_components/storages";
import { CreateStorage } from "./_components/create-storage";

export default async function StoragePage() {
  return (
    <>
      <div className="h-full flex-1 flex-col space-y-8 p-8 flex">
        <div className="flex items-center justify-between space-y-2">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              Storage Management
            </h2>
            <p className="text-muted-foreground">
              Manage your storage buckets.
            </p>
          </div>
        </div>
        <CreateStorage />
        <Storages />
      </div>
    </>
  );
}
