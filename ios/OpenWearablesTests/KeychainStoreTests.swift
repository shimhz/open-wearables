import XCTest
@testable import OpenWearables

final class KeychainStoreTests: XCTestCase {
    private let store = KeychainStore(service: "com.openwearables.tests")

    override func tearDown() {
        store.deleteAll()
        super.tearDown()
    }

    func testSetAndGet() {
        store.set("token_abc", for: "access_token")
        XCTAssertEqual(store.get("access_token"), "token_abc")
    }

    func testOverwrite() {
        store.set("old", for: "access_token")
        store.set("new", for: "access_token")
        XCTAssertEqual(store.get("access_token"), "new")
    }

    func testDelete() {
        store.set("secret", for: "refresh_token")
        store.delete("refresh_token")
        XCTAssertNil(store.get("refresh_token"))
    }

    func testDeleteAll() {
        store.set("a", for: "access_token")
        store.set("b", for: "refresh_token")
        store.set("c", for: "user_id")
        store.deleteAll()
        XCTAssertNil(store.get("access_token"))
        XCTAssertNil(store.get("refresh_token"))
        XCTAssertNil(store.get("user_id"))
    }

    func testGetMissingKeyReturnsNil() {
        XCTAssertNil(store.get("nonexistent"))
    }
}
