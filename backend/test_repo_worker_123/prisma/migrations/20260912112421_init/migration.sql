-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "passwordHash" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Character" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "level" INTEGER NOT NULL DEFAULT 1,
    "xp" INTEGER NOT NULL DEFAULT 0,
    "xpToNextLevel" INTEGER NOT NULL DEFAULT 100,
    "gold" INTEGER NOT NULL DEFAULT 0,
    "archetype" TEXT NOT NULL DEFAULT 'THE BUILDER',
    "intellect" INTEGER NOT NULL DEFAULT 10,
    "strength" INTEGER NOT NULL DEFAULT 10,
    "discipline" INTEGER NOT NULL DEFAULT 10,
    "creativity" INTEGER NOT NULL DEFAULT 10,
    "social" INTEGER NOT NULL DEFAULT 10,
    "recovery" INTEGER NOT NULL DEFAULT 10,
    "currentStreak" INTEGER NOT NULL DEFAULT 0,
    "longestStreak" INTEGER NOT NULL DEFAULT 0,
    "lastActiveDate" TEXT,
    "comboMultiplier" REAL NOT NULL DEFAULT 1.0,
    "equippedFrameId" TEXT,
    "equippedAuraId" TEXT,
    "equippedBadgeId" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Character_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Quest" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "attribute" TEXT NOT NULL,
    "difficulty" TEXT NOT NULL,
    "xpReward" INTEGER NOT NULL,
    "goldReward" INTEGER NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',
    "dueDate" DATETIME,
    "campaignId" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Quest_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Quest_campaignId_fkey" FOREIGN KEY ("campaignId") REFERENCES "Campaign" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "QuestCompletion" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "questId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "xpEarned" INTEGER NOT NULL,
    "goldEarned" INTEGER NOT NULL,
    "comboApplied" REAL NOT NULL DEFAULT 1.0,
    "completedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "QuestCompletion_questId_fkey" FOREIGN KEY ("questId") REFERENCES "Quest" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "QuestCompletion_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Campaign" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',
    "progress" INTEGER NOT NULL DEFAULT 0,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Campaign_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "CampaignStage" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "campaignId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "order" INTEGER NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'LOCKED',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "CampaignStage_campaignId_fkey" FOREIGN KEY ("campaignId") REFERENCES "Campaign" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Boss" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "maxHP" INTEGER NOT NULL DEFAULT 1000,
    "currentHP" INTEGER NOT NULL,
    "rewardXP" INTEGER NOT NULL DEFAULT 500,
    "rewardGold" INTEGER NOT NULL DEFAULT 200,
    "status" TEXT NOT NULL DEFAULT 'ACTIVE',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Boss_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "BossDamageEvent" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "bossId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "questId" TEXT,
    "damage" INTEGER NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "BossDamageEvent_bossId_fkey" FOREIGN KEY ("bossId") REFERENCES "Boss" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "BossDamageEvent_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "BossDamageEvent_questId_fkey" FOREIGN KEY ("questId") REFERENCES "Quest" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Item" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" TEXT NOT NULL,
    "price" INTEGER NOT NULL,
    "rarity" TEXT NOT NULL,
    "icon" TEXT NOT NULL DEFAULT '🎮',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "InventoryItem" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "itemId" TEXT NOT NULL,
    "equipped" BOOLEAN NOT NULL DEFAULT false,
    "purchasedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "InventoryItem_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "InventoryItem_itemId_fkey" FOREIGN KEY ("itemId") REFERENCES "Item" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Trait" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "icon" TEXT NOT NULL,
    "rarity" TEXT NOT NULL,
    "conditionKey" TEXT NOT NULL
);

-- CreateTable
CREATE TABLE "UserTrait" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "traitId" TEXT NOT NULL,
    "unlockedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "UserTrait_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "UserTrait_traitId_fkey" FOREIGN KEY ("traitId") REFERENCES "Trait" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Ability" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "requiredLevel" INTEGER NOT NULL,
    "icon" TEXT NOT NULL DEFAULT '⚡'
);

-- CreateTable
CREATE TABLE "UserAbility" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "abilityId" TEXT NOT NULL,
    "unlockedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "UserAbility_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "UserAbility_abilityId_fkey" FOREIGN KEY ("abilityId") REFERENCES "Ability" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "ActivityEvent" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ActivityEvent_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE INDEX "User_email_idx" ON "User"("email");

-- CreateIndex
CREATE UNIQUE INDEX "Character_userId_key" ON "Character"("userId");

-- CreateIndex
CREATE INDEX "Character_userId_idx" ON "Character"("userId");

-- CreateIndex
CREATE INDEX "Quest_userId_idx" ON "Quest"("userId");

-- CreateIndex
CREATE INDEX "Quest_campaignId_idx" ON "Quest"("campaignId");

-- CreateIndex
CREATE INDEX "Quest_status_idx" ON "Quest"("status");

-- CreateIndex
CREATE UNIQUE INDEX "QuestCompletion_questId_key" ON "QuestCompletion"("questId");

-- CreateIndex
CREATE INDEX "QuestCompletion_userId_idx" ON "QuestCompletion"("userId");

-- CreateIndex
CREATE INDEX "QuestCompletion_completedAt_idx" ON "QuestCompletion"("completedAt");

-- CreateIndex
CREATE INDEX "Campaign_userId_idx" ON "Campaign"("userId");

-- CreateIndex
CREATE INDEX "CampaignStage_campaignId_idx" ON "CampaignStage"("campaignId");

-- CreateIndex
CREATE INDEX "Boss_userId_idx" ON "Boss"("userId");

-- CreateIndex
CREATE INDEX "BossDamageEvent_bossId_idx" ON "BossDamageEvent"("bossId");

-- CreateIndex
CREATE INDEX "BossDamageEvent_userId_idx" ON "BossDamageEvent"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "Item_name_key" ON "Item"("name");

-- CreateIndex
CREATE INDEX "InventoryItem_userId_idx" ON "InventoryItem"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "InventoryItem_userId_itemId_key" ON "InventoryItem"("userId", "itemId");

-- CreateIndex
CREATE UNIQUE INDEX "Trait_name_key" ON "Trait"("name");

-- CreateIndex
CREATE INDEX "UserTrait_userId_idx" ON "UserTrait"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "UserTrait_userId_traitId_key" ON "UserTrait"("userId", "traitId");

-- CreateIndex
CREATE UNIQUE INDEX "Ability_name_key" ON "Ability"("name");

-- CreateIndex
CREATE INDEX "UserAbility_userId_idx" ON "UserAbility"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "UserAbility_userId_abilityId_key" ON "UserAbility"("userId", "abilityId");

-- CreateIndex
CREATE INDEX "ActivityEvent_userId_idx" ON "ActivityEvent"("userId");

-- CreateIndex
CREATE INDEX "ActivityEvent_createdAt_idx" ON "ActivityEvent"("createdAt");

-- CreateIndex
CREATE INDEX "ActivityEvent_type_idx" ON "ActivityEvent"("type");
