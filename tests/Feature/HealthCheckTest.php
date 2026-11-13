<?php

namespace Tests\Feature;

use Tests\TestCase;

class HealthCheckTest extends TestCase
{
    public function test_health_check(): void
    {
        $this->getJson('api/health')
            ->assertOk()
            ->assertExactJson(['status' => 'ok']);
    }

    public function test_cors_check(): void
    {
        $origin = config('cors.allowed_origins')[0];

        $this->getJson('api/health', ['Origin' => $origin])
            ->assertOk()
            ->assertHeader('Access-Control-Allow-Origin', $origin);
    }
}
