"use client";

import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const { data: session } = useSession();

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold">Profile</h1>
      <p className="mt-4">
        Welcome, {session?.user?.name ?? "Guest"}!
      </p>
      <p>Email: {session?.user?.email}</p>
      <Button onClick={() => signOut()} className="mt-4">
        Sign Out
      </Button>
    </div>
  );
}
