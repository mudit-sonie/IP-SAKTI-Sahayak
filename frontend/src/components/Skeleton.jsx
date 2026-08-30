import styles from "./Skeleton.module.css";

const cx = (...c) => c.filter(Boolean).join(" ");

export function SkeletonLine({ w = "100%" }) {
  return <span className={styles.line} style={{ width: w }} />;
}

/** Loading placeholder for the Result answer card. */
export default function AnswerSkeleton() {
  return (
    <div className={cx(styles.wrap, "stack")} aria-live="polite" aria-busy="true">
      <div className={styles.head}>
        <SkeletonLine w="120px" />
        <SkeletonLine w="90px" />
      </div>
      <div className={styles.para}>
        <SkeletonLine />
        <SkeletonLine w="94%" />
        <SkeletonLine w="97%" />
        <SkeletonLine w="72%" />
      </div>
      <p className={styles.note}>
        Retrieving statutory provisions and grounding the answer…
      </p>
    </div>
  );
}
