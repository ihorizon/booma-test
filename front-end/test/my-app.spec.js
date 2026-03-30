import { describe, it } from 'vitest';
import { MyApp } from '../src/my-app';
import { createFixture } from '@aurelia/testing';

describe('my-app', () => {
  it('hydrates without template compiler errors', async () => {
    const { appHost } = await createFixture(
      '<my-app></my-app>',
      {},
      [MyApp],
    ).started;

    const element = appHost.querySelector('my-app');
    if (element === null) {
      throw new Error('Expected to find my-app element in host');
    }
  });
});
