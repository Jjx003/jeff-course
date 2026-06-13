declare global {
  namespace App {
    interface Locals {
      user: {
        id: string;
        name: string;
        role: 'admin' | 'learner';
      } | null;
      hasUsers: boolean;
    }

    interface PageData {
      user?: App.Locals['user'];
      hasUsers?: boolean;
    }
  }
}

export {};
