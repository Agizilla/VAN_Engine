export interface Intent {
  name: string;
  confidence: number;
  skill: string;
}

export interface Skill {
  name: string;
  description: string;
  canHandle: (intent: string) => boolean;
  execute: (intent: Intent, context: any) => Promise<any>;
}

export class SkillRouter {
  private skills: Map<string, Skill> = new Map();

  register(skill: Skill): void {
    this.skills.set(skill.name, skill);
  }

  async route(intent: Intent, context: any): Promise<any> {
    const matchedSkills: Skill[] = [];

    for (const [, skill] of this.skills) {
      if (skill.canHandle(intent.name)) {
        matchedSkills.push(skill);
      }
    }

    if (matchedSkills.length === 0) {
      return {
        handled: false,
        intent: intent.name,
        message: `No skill found for intent: ${intent.name}`
      };
    }

    matchedSkills.sort((a, b) => {
      const aScore = a.name === intent.skill ? 1 : 0;
      const bScore = b.name === intent.skill ? 1 : 0;
      return bScore - aScore;
    });

    const selected = matchedSkills[0];
    const result = await selected.execute(intent, context);

    return {
      handled: true,
      intent: intent.name,
      skill: selected.name,
      result
    };
  }

  getSkills(): Skill[] {
    return Array.from(this.skills.values());
  }
}
