// Copyright (C) 2024-2026 Tobias Rosenbaum
//
// This file is part of Applire.
//
// Applire is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Applire is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with Applire. If not, see <https://www.gnu.org/licenses/>.

import { AddRoleView } from "@/components/profile/AddRoleView";
import { ProfileImportView } from "@/components/profile/ProfileImportView";
import { ProfileUpdateChooser } from "@/components/profile/ProfileUpdateChooser";

interface PageProps {
  searchParams: Promise<{ action?: string }>;
}

export default async function ProfileUpdatePage({ searchParams }: PageProps) {
  const { action } = await searchParams;

  if (action === "upload") return <ProfileImportView />;
  if (action === "add-role") return <AddRoleView />;
  return <ProfileUpdateChooser />;
}
