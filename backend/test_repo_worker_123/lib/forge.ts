// LIFE//OS — Quest Forge
// Deterministic AI-assisted quest generation system
// No external API required — uses pattern matching and curated templates

import {
  ATTRIBUTE_KEYWORDS,
  DIFFICULTY_XP,
  DIFFICULTY_GOLD,
  Attribute,
} from './constants';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ForgeInput {
  goal: string;
  userId: string;
}

export interface ForgedQuest {
  title: string;
  description: string;
  attribute: Attribute;
  difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'EPIC';
  xpReward: number;
  goldReward: number;
}

export interface ForgedCampaign {
  name: string;
  description: string;
  stages: Array<{ name: string; description: string; order: number }>;
  quests: ForgedQuest[];
}

// ─── Campaign Templates ───────────────────────────────────────────────────────

const CAMPAIGN_TEMPLATES: Record<string, ForgedCampaign> = {
  programming: {
    name: 'BECOME A FULL-STACK DEVELOPER',
    description: 'Master the complete stack from frontend to production deployment.',
    stages: [
      { name: 'Foundations', description: 'Core programming concepts', order: 1 },
      { name: 'Frontend', description: 'HTML, CSS, JavaScript', order: 2 },
      { name: 'Backend', description: 'Node.js and APIs', order: 3 },
      { name: 'Database', description: 'SQL and data modeling', order: 4 },
      { name: 'Production', description: 'Deploy a real project', order: 5 },
    ],
    quests: [
      { title: 'Complete JavaScript fundamentals', description: 'Variables, functions, loops, objects', attribute: 'INTELLECT', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
      { title: 'Build a React component library', description: '10 reusable UI components', attribute: 'INTELLECT', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Write a REST API from scratch', description: 'Express.js with full CRUD', attribute: 'INTELLECT', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Design a database schema', description: 'Model a real application', attribute: 'INTELLECT', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
      { title: 'Deploy to production', description: 'Ship a full-stack app live', attribute: 'DISCIPLINE', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
    ],
  },
  fitness: {
    name: 'PHYSICAL TRANSFORMATION',
    description: 'Build a strong, capable body through consistent training.',
    stages: [
      { name: 'Foundation', description: 'Build the habit', order: 1 },
      { name: 'Strength', description: 'Build base strength', order: 2 },
      { name: 'Endurance', description: 'Cardiovascular capacity', order: 3 },
      { name: 'Advanced', description: 'Elite performance', order: 4 },
    ],
    quests: [
      { title: 'Complete 30 workouts', description: 'Consistency is the foundation', attribute: 'STRENGTH', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Run 5km without stopping', description: 'Build aerobic base', attribute: 'STRENGTH', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
      { title: 'Master the big three lifts', description: 'Squat, bench, deadlift', attribute: 'STRENGTH', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Train 7 days straight', description: 'One week discipline streak', attribute: 'DISCIPLINE', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
    ],
  },
  creativity: {
    name: 'CREATIVE MASTERY',
    description: 'Develop your creative voice and build a portfolio of work.',
    stages: [
      { name: 'Exploration', description: 'Find your medium', order: 1 },
      { name: 'Practice', description: 'Daily creation habit', order: 2 },
      { name: 'Portfolio', description: 'Build a body of work', order: 3 },
      { name: 'Publish', description: 'Share with the world', order: 4 },
    ],
    quests: [
      { title: 'Create something every day for 30 days', description: 'The creative habit', attribute: 'CREATIVITY', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Finish a complete creative project', description: 'Start and finish something real', attribute: 'CREATIVITY', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
      { title: 'Share your work publicly', description: 'Publish online', attribute: 'SOCIAL', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
    ],
  },
  learning: {
    name: 'LIFELONG SCHOLAR',
    description: 'Build a systematic learning practice and compound knowledge.',
    stages: [
      { name: 'Reading habit', description: 'Read every day', order: 1 },
      { name: 'Note-taking system', description: 'Capture what you learn', order: 2 },
      { name: 'Deep dives', description: 'Master one subject', order: 3 },
      { name: 'Teaching', description: 'Explain what you know', order: 4 },
    ],
    quests: [
      { title: 'Read for 20 minutes daily for 30 days', description: 'Build the reading habit', attribute: 'INTELLECT', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
      { title: 'Finish one non-fiction book', description: 'Complete a full book', attribute: 'INTELLECT', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Build a personal knowledge base', description: 'Document what you learn', attribute: 'DISCIPLINE', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
      { title: 'Teach someone something you learned', description: 'Explaining solidifies knowledge', attribute: 'SOCIAL', difficulty: 'MEDIUM', xpReward: 60, goldReward: 25 },
    ],
  },
  business: {
    name: 'BUILD YOUR EMPIRE',
    description: 'Launch and grow a business or side project.',
    stages: [
      { name: 'Idea validation', description: 'Is this worth building?', order: 1 },
      { name: 'MVP', description: 'Build the smallest useful version', order: 2 },
      { name: 'Launch', description: 'Get it in front of people', order: 3 },
      { name: 'Growth', description: 'Scale and iterate', order: 4 },
    ],
    quests: [
      { title: 'Talk to 10 potential customers', description: 'Validate the problem', attribute: 'SOCIAL', difficulty: 'HARD', xpReward: 120, goldReward: 60 },
      { title: 'Build a working prototype', description: 'Something real people can use', attribute: 'INTELLECT', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
      { title: 'Launch publicly', description: 'Ship it to the world', attribute: 'DISCIPLINE', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
      { title: 'Get first paying customer', description: 'Money validates the business', attribute: 'SOCIAL', difficulty: 'EPIC', xpReward: 250, goldReward: 150 },
    ],
  },
};

// ─── Goal Classifier ──────────────────────────────────────────────────────────

function classifyGoal(goal: string): keyof typeof CAMPAIGN_TEMPLATES {
  const lower = goal.toLowerCase();
  
  if (/program|code|develop|software|web|app|tech|javascript|python|react/.test(lower)) {
    return 'programming';
  }
  if (/fit|gym|workout|run|sport|body|weight|muscle|health|exercise/.test(lower)) {
    return 'fitness';
  }
  if (/creat|art|design|music|write|draw|photo|film|craft|build/.test(lower)) {
    return 'creativity';
  }
  if (/learn|study|read|book|knowledge|skill|master|understand/.test(lower)) {
    return 'learning';
  }
  if (/business|startup|money|product|launch|company|entrepreneur/.test(lower)) {
    return 'business';
  }
  
  // Default: generate based on keyword matching
  return 'learning';
}

// ─── Attribute Detector ───────────────────────────────────────────────────────

function detectAttribute(text: string): Attribute {
  const lower = text.toLowerCase();
  
  for (const [attr, keywords] of Object.entries(ATTRIBUTE_KEYWORDS)) {
    if (keywords.some((kw) => lower.includes(kw))) {
      return attr as Attribute;
    }
  }
  
  return 'INTELLECT';
}

// ─── Main Forge Function ──────────────────────────────────────────────────────

export function forgeFromGoal(input: ForgeInput): ForgedCampaign {
  const templateKey = classifyGoal(input.goal);
  const template = CAMPAIGN_TEMPLATES[templateKey];
  
  // Customize name based on user input if possible
  const customName = input.goal.length > 5 && input.goal.length < 60
    ? input.goal.toUpperCase()
    : template.name;

  return {
    ...template,
    name: customName,
  };
}

// ─── Single Quest Generator ───────────────────────────────────────────────────

export function forgeQuest(description: string): ForgedQuest {
  const attribute = detectAttribute(description);
  const lower = description.toLowerCase();
  
  let difficulty: 'EASY' | 'MEDIUM' | 'HARD' | 'EPIC' = 'MEDIUM';
  if (/easy|quick|simple|short/.test(lower)) difficulty = 'EASY';
  if (/challenge|hard|difficult|intense/.test(lower)) difficulty = 'HARD';
  if (/epic|massive|major|big|complete|master/.test(lower)) difficulty = 'EPIC';

  return {
    title: description.charAt(0).toUpperCase() + description.slice(1),
    description: '',
    attribute,
    difficulty,
    xpReward: DIFFICULTY_XP[difficulty],
    goldReward: DIFFICULTY_GOLD[difficulty],
  };
}
