import { FileUpload } from "@/components/file-upload";

type StorageDetailsPageProps = {
  params: {
    storageId: string;
  };
};

export default async function StorageDetailsPage({
  params,
}: StorageDetailsPageProps) {
  const { storageId } = params;

  // In a real application, you would fetch storage details here
  // const storageDetails = await getStorageDetails(storageId);

  return (
    <div className="h-full flex-1 flex-col space-y-8 p-8 flex">
      <div className="flex items-center justify-between space-y-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Storage Details
          </h2>
          <p className="text-muted-foreground">
            Manage files for storage ID: {storageId}
          </p>
        </div>
      </div>
      <div className="border rounded-md p-4">
        <h3 className="text-lg font-semibold mb-4">Upload New File</h3>
        <FileUpload storageId={storageId} />
      </div>
      {/* A component to list existing files would go here */}
    </div>
  );
}
