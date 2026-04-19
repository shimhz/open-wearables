.PHONY: generate build test run clean

generate:
	xcodegen generate

build: generate
	xcodebuild -project OpenWearables.xcodeproj -scheme OpenWearables -destination 'platform=iOS Simulator,name=iPhone 16' build

test: generate
	xcodebuild -project OpenWearables.xcodeproj -scheme OpenWearablesTests -destination 'platform=iOS Simulator,name=iPhone 16' test

run: generate
	open OpenWearables.xcodeproj

clean:
	rm -rf DerivedData build
	rm -rf OpenWearables.xcodeproj
