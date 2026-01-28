import * as https from 'https';
import * as fs from 'fs';
import type { Release } from '../types';

const REPO_OWNER = 'Moksa1123';
const REPO_NAME = 'taiwan-invoice';
const API_BASE = 'https://api.github.com';

/**
 * Fetch all releases from GitHub
 */
export async function fetchReleases(): Promise<Release[]> {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${REPO_OWNER}/${REPO_NAME}/releases`,
      headers: {
        'User-Agent': 'taiwan-invoice-skill-cli',
        'Accept': 'application/vnd.github.v3+json'
      }
    };

    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(new Error('Failed to parse GitHub response'));
          }
        } else if (res.statusCode === 404) {
          resolve([]);
        } else {
          reject(new Error(`GitHub API error: ${res.statusCode}`));
        }
      });
    }).on('error', reject);
  });
}

/**
 * Get the latest release
 */
export async function getLatestRelease(): Promise<Release | null> {
  const releases = await fetchReleases();
  return releases.length > 0 ? releases[0] : null;
}

/**
 * Download a file from URL to destination
 */
export async function downloadRelease(url: string, dest: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);

    const request = (downloadUrl: string) => {
      https.get(downloadUrl, {
        headers: {
          'User-Agent': 'taiwan-invoice-skill-cli',
          'Accept': 'application/octet-stream'
        }
      }, (res) => {
        // Handle redirects
        if (res.statusCode === 302 || res.statusCode === 301) {
          const redirectUrl = res.headers.location;
          if (redirectUrl) {
            request(redirectUrl);
            return;
          }
        }

        if (res.statusCode !== 200) {
          file.close();
          fs.unlinkSync(dest);
          reject(new Error(`Download failed: ${res.statusCode}`));
          return;
        }

        res.pipe(file);
        file.on('finish', () => {
          file.close();
          resolve();
        });
      }).on('error', (err) => {
        file.close();
        fs.unlinkSync(dest);
        reject(err);
      });
    };

    request(url);
  });
}

/**
 * Get the ZIP asset URL from a release
 */
export function getAssetUrl(release: Release): string | null {
  const zipAsset = release.assets.find(
    asset => asset.name.endsWith('.zip') || asset.name.includes('source')
  );
  return zipAsset?.browser_download_url || null;
}

/**
 * Get source code ZIP URL (fallback)
 */
export function getSourceZipUrl(release: Release): string {
  return `https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/tags/${release.tag_name}.zip`;
}
