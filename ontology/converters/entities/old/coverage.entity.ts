import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvEntity } from '@vsolv/dev-kit/nest';
import { Column, CreateDateColumn, JoinColumn, ManyToOne, OneToMany, PrimaryColumn, UpdateDateColumn } from 'typeorm';
import { ExclusionEntity } from '../../exclusion';
import { PolicyEntity } from '../../policy';
import { CoverageAggregate } from '../models';

@VsolvEntity({ prefix: 'cov', name: 'warranty_coverage' }, 'tenant')
export class CoverageEntity {
  @PrimaryColumn()
  id!: string;

  @Column()
  title!: string;

  @Column({ nullable: true })
  referenceId!: string | null;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  deductible!: number;

  @Column()
  liabilityLimit!: number;

  @Column()
  policyId!: string;

  @JoinColumn({ name: 'policyId' })
  @ManyToOne(() => PolicyEntity)
  policy?: PolicyEntity;

  @OneToMany(() => ExclusionEntity, exc => exc.coverage)
  exclusions?: ExclusionEntity[];

  toAggregate(publisher?: EventPublisher): CoverageAggregate {
    return mergeObjectContext(
      new CoverageAggregate({
        id: this.id,
        title: this.title,
        referenceId: this.referenceId,

        created: this.created,
        modified: this.modified,

        deductible: this.deductible,
        liabilityLimit: this.liabilityLimit,

        exclusions: this.exclusions?.map(exc => exc.toAggregate(publisher)) ?? undefined,
      }),
      publisher
    );
  }
}
