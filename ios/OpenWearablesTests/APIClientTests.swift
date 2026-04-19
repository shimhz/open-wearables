import XCTest
@testable import OpenWearables

final class EndpointTests: XCTestCase {
    func testDailyFrameEndpointBuildsCorrectURL() throws {
        let userId = UUID(uuidString: "123e4567-e89b-12d3-a456-426614174000")!
        let endpoint = Endpoints.dailyFrame(userId: userId, startDate: "2026-04-01", endDate: "2026-04-15")

        let request = try endpoint.urlRequest(baseURL: URL(string: "http://localhost:8000")!, token: "test_token")

        XCTAssertEqual(request.httpMethod, "GET")
        XCTAssertTrue(request.url!.absoluteString.contains("/insights/daily-frame"))
        XCTAssertTrue(request.url!.absoluteString.contains("start_date=2026-04-01"))
        XCTAssertTrue(request.url!.absoluteString.contains("end_date=2026-04-15"))
        XCTAssertEqual(request.value(forHTTPHeaderField: "Authorization"), "Bearer test_token")
    }

    func testRedeemCodeEndpointIsPost() throws {
        let endpoint = Endpoints.redeemCode("ABCD1234")
        let request = try endpoint.urlRequest(baseURL: URL(string: "http://localhost:8000")!, token: nil)

        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertTrue(request.url!.absoluteString.contains("/invitation-code/redeem"))
        XCTAssertNil(request.value(forHTTPHeaderField: "Authorization"))
        XCTAssertNotNil(request.httpBody)
    }

    func testRefreshTokenEndpointShape() throws {
        let endpoint = Endpoints.refreshToken("rt-abc123")
        let request = try endpoint.urlRequest(baseURL: URL(string: "http://localhost:8000")!, token: nil)

        XCTAssertEqual(request.httpMethod, "POST")
        XCTAssertTrue(request.url!.absoluteString.contains("/token/refresh"))
    }
}
