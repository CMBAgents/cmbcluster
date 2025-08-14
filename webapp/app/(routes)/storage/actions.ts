"use server";

import createApiClient from "packages/sdk/api";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

const api = createApiClient({
  baseUrl: "http://localhost:8000",
});

type State = {
  message: string;
  error?: string;
};

export async function createStorage(
  prevState: State,
  formData: FormData
): Promise<State> {
  const custom_name = formData.get("custom_name") as string;
  const storage_class = formData.get("storage_class") as string;
  const location = formData.get("location") as string;

  const { error } = await api.POST("/storage/create", {
    body: {
      storage_type: "cloud_storage",
      storage_class,
      custom_name,
      location,
    },
  });

  if (error) {
    console.error(error);
    return {
      message: "Failed to create storage.",
      error: error.message,
    };
  }

  revalidatePath("/storage");
  redirect("/storage");
}
